import { create } from "zustand";
import { persist } from "zustand/middleware";

const getItemId = (item) => item?._id || item?.id;

export const useCartStore = create(
	persist(
		(set) => ({
			cart: [],
			wishlist: [],
			isCartOpen: false,

			addToCart: (product, quantity = 1) =>
				set((state) => {
					const id = getItemId(product);
					const existing = state.cart.find((item) => getItemId(item) === id);

					if (existing) {
						return {
							cart: state.cart.map((item) =>
								getItemId(item) === id ? { ...item, quantity: item.quantity + quantity } : item
							),
						};
					}

					return { cart: [...state.cart, { ...product, quantity }] };
				}),

			removeFromCart: (id) =>
				set((state) => ({ cart: state.cart.filter((item) => getItemId(item) !== id) })),

			updateQuantity: (id, quantity) =>
				set((state) => ({
					cart: state.cart.map((item) =>
						getItemId(item) === id ? { ...item, quantity: Math.max(1, quantity) } : item
					),
				})),

			clearCart: () => set({ cart: [] }),

			toggleWishlist: (product) =>
				set((state) => {
					const id = getItemId(product);
					const saved = state.wishlist.some((item) => getItemId(item) === id);
					return {
						wishlist: saved
							? state.wishlist.filter((item) => getItemId(item) !== id)
							: [...state.wishlist, product],
					};
				}),

			openCart: () => set({ isCartOpen: true }),
			closeCart: () => set({ isCartOpen: false }),
		}),
		{
			name: "velora-store",
			partialize: (state) => ({ cart: state.cart, wishlist: state.wishlist }),
		}
	)
);
