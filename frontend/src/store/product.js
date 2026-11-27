import { create } from "zustand";

const jsonHeaders = { "Content-Type": "application/json" };

export const useProductStore = create((set) => ({
	products: [],
	isLoading: false,
	error: null,

	setProducts: (products) => set({ products }),

	createProduct: async (newProduct) => {
		if (!newProduct.name || !newProduct.image || !newProduct.price) {
			return { success: false, message: "Please fill in all fields." };
		}

		try {
			const res = await fetch("/api/products", {
				method: "POST",
				headers: jsonHeaders,
				body: JSON.stringify(newProduct),
			});
			const data = await res.json();
			if (!res.ok || !data.success) {
				return { success: false, message: data.message || "Unable to create the product." };
			}

			set((state) => ({ products: [...state.products, data.data], error: null }));
			return { success: true, message: "Product created successfully" };
		} catch {
			return { success: false, message: "Unable to reach the store. Please try again." };
		}
	},

	fetchProducts: async () => {
		set({ isLoading: true, error: null });
		try {
			const res = await fetch("/api/products");
			if (!res.ok) throw new Error("Request failed");

			const data = await res.json();
			set({ products: Array.isArray(data.data) ? data.data : [], isLoading: false });
		} catch {
			set({ products: [], isLoading: false, error: "Unable to load products." });
		}
	},

	deleteProduct: async (pid) => {
		try {
			const res = await fetch(`/api/products/${pid}`, { method: "DELETE" });
			const data = await res.json();
			if (!data.success) return { success: false, message: data.message };

			set((state) => ({
				products: state.products.filter((product) => product._id !== pid),
			}));
			return { success: true, message: data.message };
		} catch {
			return { success: false, message: "Unable to reach the store. Please try again." };
		}
	},

	updateProduct: async (pid, updatedProduct) => {
		try {
			const res = await fetch(`/api/products/${pid}`, {
				method: "PUT",
				headers: jsonHeaders,
				body: JSON.stringify(updatedProduct),
			});
			const data = await res.json();
			if (!data.success) return { success: false, message: data.message };

			set((state) => ({
				products: state.products.map((product) => (product._id === pid ? data.data : product)),
			}));
			return { success: true, message: data.message };
		} catch {
			return { success: false, message: "Unable to reach the store. Please try again." };
		}
	},
}));
