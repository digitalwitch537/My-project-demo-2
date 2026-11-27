import { useEffect } from "react";
import { Box, useColorModeValue } from "@chakra-ui/react";
import { Route, Routes, useLocation } from "react-router-dom";

import CartDrawer from "./components/CartDrawer";
import Footer from "./components/Footer";
import Navbar from "./components/Navbar";
import CartPage from "./pages/CartPage";
import CheckoutPage from "./pages/CheckoutPage";
import CreatePage from "./pages/CreatePage";
import HomePage from "./pages/HomePage";
import NotFoundPage from "./pages/NotFoundPage";
import WishlistPage from "./pages/WishlistPage";

const ScrollManager = () => {
	const { pathname, hash } = useLocation();

	useEffect(() => {
		const timer = setTimeout(() => {
			if (hash) {
				document.querySelector(hash)?.scrollIntoView({ behavior: "smooth" });
			} else {
				window.scrollTo({ top: 0, behavior: "auto" });
			}
		}, 60);

		return () => clearTimeout(timer);
	}, [pathname, hash]);

	return null;
};

function App() {
	const bg = useColorModeValue("velora.canvas", "velora.night");

	return (
		<Box minH="100vh" bg={bg} display="flex" flexDirection="column">
			<ScrollManager />
			<Navbar />
			<Box as="main" flex="1">
				<Routes>
					<Route path="/" element={<HomePage />} />
					<Route path="/create" element={<CreatePage />} />
					<Route path="/studio" element={<CreatePage />} />
					<Route path="/cart" element={<CartPage />} />
					<Route path="/checkout" element={<CheckoutPage />} />
					<Route path="/wishlist" element={<WishlistPage />} />
					<Route path="*" element={<NotFoundPage />} />
				</Routes>
			</Box>
			<Footer />
			<CartDrawer />
		</Box>
	);
}

export default App;
