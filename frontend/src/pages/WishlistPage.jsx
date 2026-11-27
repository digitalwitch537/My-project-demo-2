import {
	Box,
	Button,
	Container,
	Heading,
	SimpleGrid,
	Text,
	useColorModeValue,
	VStack,
} from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";
import { FiArrowRight, FiHeart } from "react-icons/fi";
import ProductCard from "../components/ProductCard";
import { useCartStore } from "../store/cart";

const WishlistPage = () => {
	const wishlist = useCartStore((state) => state.wishlist);
	const muted = useColorModeValue("velora.muted", "velora.mutedDark");

	return (
		<Container maxW="1280px" px={{ base: 4, md: 6, lg: 8 }} py={{ base: 12, md: 20 }}>
			<VStack align="flex-start" spacing={2} mb={10}>
				<Text fontSize="10px" fontWeight="700" letterSpacing="0.24em" color="velora.accent">
					SAVED FOR LATER
				</Text>
				<Heading fontSize={{ base: "4xl", md: "5xl" }}>Your wishlist</Heading>
				<Text color={muted} fontSize="sm">
					{wishlist.length} {wishlist.length === 1 ? "piece" : "pieces"} you love, kept close.
				</Text>
			</VStack>

			{wishlist.length === 0 ? (
				<VStack spacing={6} textAlign="center" py={20}>
					<Box w={24} h={24} borderRadius="full" bg="velora.accentSoft" color="velora.accent" display="grid" placeItems="center" fontSize="4xl">
						<FiHeart />
					</Box>
					<Heading fontSize={{ base: "3xl", md: "4xl" }}>Nothing saved yet</Heading>
					<Text color={muted} fontSize="sm" maxW="420px">
						Tap the heart on any piece in the edit to keep it here for later.
					</Text>
					<Button as={RouterLink} to="/#edit" variant="accent" rightIcon={<FiArrowRight />}>
						Explore the edit
					</Button>
				</VStack>
			) : (
				<SimpleGrid columns={{ base: 1, sm: 2, lg: 3, xl: 4 }} spacing={6}>
					{wishlist.map((product, index) => (
						<ProductCard key={product._id || product.id || index} product={product} index={index} />
					))}
				</SimpleGrid>
			)}
		</Container>
	);
};

export default WishlistPage;
