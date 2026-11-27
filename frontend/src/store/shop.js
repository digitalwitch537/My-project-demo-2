import { create } from "zustand";

export const useShopStore = create((set) => ({
	search: "",
	category: "All",
	sort: "featured",

	setSearch: (search) => set({ search }),
	setCategory: (category) => set({ category }),
	setSort: (sort) => set({ sort }),
	resetFilters: () => set({ search: "", category: "All", sort: "featured" }),
}));
