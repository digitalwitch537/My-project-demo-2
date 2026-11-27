import { BRAND } from "../brand";

export const CATEGORY_FILTERS = ["All", ...BRAND.categories];

export const formatPrice = (value) =>
	new Intl.NumberFormat("en-US", {
		style: "currency",
		currency: "USD",
		minimumFractionDigits: 2,
	}).format(Number(value) || 0);

const CATEGORY_KEYWORDS = [
	["Home", /lamp|chair|sofa|vase|table|decor|cushion|light|home|mirror|ceramic/i],
	["Style", /bag|watch|shoe|jacket|shirt|jewel|scarf|sunglass|style|coat|denim/i],
	["Tech", /phone|headphone|speaker|camera|keyboard|laptop|tech|audio|device|watch/i],
	["Wellness", /candle|skin|serum|soap|yoga|wellness|oil|bath|fragrance|diffuser/i],
];

export const getProductCategory = (product, index = 0) => {
	if (CATEGORY_FILTERS.includes(product?.category)) return product.category;

	const name = product?.name || "";
	const match = CATEGORY_KEYWORDS.find(([, pattern]) => pattern.test(name));
	if (match) return match[0];

	return BRAND.categories[index % BRAND.categories.length];
};

export const filterProducts = (products, { search, category, sort }) => {
	const term = search.trim().toLowerCase();

	const result = products
		.map((product, index) => ({ ...product, category: getProductCategory(product, index) }))
		.filter((product) => category === "All" || product.category === category)
		.filter(
			(product) =>
				!term ||
				(product.name || "").toLowerCase().includes(term) ||
				product.category.toLowerCase().includes(term)
		);

	if (sort === "price-asc") result.sort((a, b) => Number(a.price) - Number(b.price));
	if (sort === "price-desc") result.sort((a, b) => Number(b.price) - Number(a.price));
	if (sort === "name") result.sort((a, b) => a.name.localeCompare(b.name));

	return result;
};
