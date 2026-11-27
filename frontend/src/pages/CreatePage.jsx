import { useEffect, useState } from "react";
import {
	Box,
	Button,
	Container,
	Flex,
	FormControl,
	FormLabel,
	Grid,
	Heading,
	HStack,
	Image,
	Input,
	SimpleGrid,
	Text,
	useColorModeValue,
	useToast,
	VStack,
} from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";
import { FiArrowLeft, FiArrowRight, FiBox, FiImage, FiPlus, FiTag } from "react-icons/fi";
import ProductCard from "../components/ProductCard";
import { BRAND } from "../brand";
import { useProductStore } from "../store/product";
import { formatPrice } from "../utils/catalog";

const emptyProduct = { name: "", price: "", image: "" };

const CreatePage = () => {
	const [newProduct, setNewProduct] = useState(emptyProduct);
	const toast = useToast();

	const products = useProductStore((state) => state.products);
	const fetchProducts = useProductStore((state) => state.fetchProducts);
	const createProduct = useProductStore((state) => state.createProduct);

	const surface = useColorModeValue("velora.surface", "velora.nightSurface");
	const muted = useColorModeValue("velora.muted", "velora.mutedDark");
	const borderColor = useColorModeValue("velora.line", "velora.lineDark");

	useEffect(() => {
		fetchProducts();
	}, [fetchProducts]);

	const handleAddProduct = async () => {
		const { success, message } = await createProduct(newProduct);
		toast({
			title: success ? "Product published" : "Something went wrong",
			description: success ? "Your new piece is live in the edit." : message,
			status: success ? "success" : "error",
			duration: 3000,
			isClosable: true,
		});
		if (success) setNewProduct(emptyProduct);
	};

	const inventoryValue = products.reduce((total, product) => total + Number(product.price || 0), 0);

	return (
		<Container maxW="1280px" px={{ base: 4, md: 6, lg: 8 }} py={{ base: 10, md: 16 }}>
			<VStack align="flex-start" spacing={3} mb={10}>
				<HStack fontSize="xs" color={muted} spacing={2}>
					<Text as={RouterLink} to="/" _hover={{ color: "velora.accent" }}>{BRAND.name} Store</Text>
					<Text>/</Text>
					<Text color="velora.accent">Studio</Text>
				</HStack>
				<Flex justify="space-between" align="flex-end" w="full" gap={6} direction={{ base: "column", md: "row" }}>
					<Box>
						<Heading fontSize={{ base: "4xl", md: "5xl" }}>Studio</Heading>
						<Text color={muted} fontSize="sm" mt={2}>
							Add new pieces and manage the catalog behind the edit.
						</Text>
					</Box>
					<Button as={RouterLink} to="/" variant="outlineInk" leftIcon={<FiArrowLeft />}>
						Back to store
					</Button>
				</Flex>
			</VStack>

			<SimpleGrid columns={{ base: 1, sm: 3 }} spacing={4} mb={10}>
				{[
					{ label: "Live products", value: products.length, icon: FiBox },
					{ label: "Catalog value", value: formatPrice(inventoryValue), icon: FiTag },
					{ label: "Collections", value: BRAND.categories.length + 1, icon: FiImage },
				].map((stat) => (
					<Flex
						key={stat.label}
						align="center"
						gap={4}
						p={5}
						bg={surface}
						border="1px solid"
						borderColor={borderColor}
						borderRadius="2xl"
					>
						<Box w={11} h={11} borderRadius="full" bg="velora.accentSoft" color="velora.accent" display="grid" placeItems="center">
							<stat.icon />
						</Box>
						<Box>
							<Text fontSize="xs" color={muted} letterSpacing="0.08em" textTransform="uppercase">{stat.label}</Text>
							<Text fontFamily="heading" fontSize="2xl">{stat.value}</Text>
						</Box>
					</Flex>
				))}
			</SimpleGrid>

			<Grid templateColumns={{ base: "1fr", lg: "1.1fr 0.9fr" }} gap={6} mb={16}>
				<Box p={{ base: 6, md: 8 }} bg={surface} border="1px solid" borderColor={borderColor} borderRadius="2xl">
					<HStack spacing={3} mb={6}>
						<Box w={9} h={9} borderRadius="full" bg="velora.accentSoft" color="velora.accent" display="grid" placeItems="center">
							<FiPlus />
						</Box>
						<Box>
							<Heading fontSize="2xl">Add a new piece</Heading>
							<Text fontSize="xs" color={muted}>Every detail counts.</Text>
						</Box>
					</HStack>
					<VStack spacing={5} align="stretch">
						<FormControl>
							<FormLabel fontSize="xs" letterSpacing="0.08em" textTransform="uppercase" color={muted}>Product name</FormLabel>
							<Input
								value={newProduct.name}
								onChange={(event) => setNewProduct({ ...newProduct, name: event.target.value })}
								placeholder="e.g. Arlo Ceramic Vase"
							/>
						</FormControl>
						<FormControl>
							<FormLabel fontSize="xs" letterSpacing="0.08em" textTransform="uppercase" color={muted}>Price (USD)</FormLabel>
							<Input
								type="number"
								value={newProduct.price}
								onChange={(event) => setNewProduct({ ...newProduct, price: event.target.value })}
								placeholder="0.00"
							/>
						</FormControl>
						<FormControl>
							<FormLabel fontSize="xs" letterSpacing="0.08em" textTransform="uppercase" color={muted}>Image URL</FormLabel>
							<Input
								value={newProduct.image}
								onChange={(event) => setNewProduct({ ...newProduct, image: event.target.value })}
								placeholder="https://..."
							/>
						</FormControl>
						<Button variant="accent" size="lg" w="full" leftIcon={<FiPlus />} onClick={handleAddProduct}>
							Publish product
						</Button>
					</VStack>
				</Box>

				<Box
					position="relative"
					overflow="hidden"
					borderRadius="2xl"
					border="1px solid"
					borderColor={borderColor}
					bg={surface}
					minH="480px"
				>
					<Box h="62%" bgGradient="linear(135deg, velora.accentSoft, velora.line)" position="relative">
						{newProduct.image ? (
							<Image src={newProduct.image} alt="Product preview" w="full" h="full" objectFit="cover" />
						) : (
							<VStack h="full" spacing={3} justify="center" color="velora.accent">
								<FiImage size={36} />
								<Text fontSize="xs" letterSpacing="0.16em" textTransform="uppercase">Live preview</Text>
							</VStack>
						)}
						<Box position="absolute" top={4} left={4} bg="velora.ink" color="white" px={3} py={1} borderRadius="full" fontSize="9px" letterSpacing="0.16em">
							PREVIEW
						</Box>
					</Box>
					<Box p={6}>
						<Text fontSize="10px" letterSpacing="0.2em" color="velora.accent" textTransform="uppercase">New arrival</Text>
						<Heading fontSize="2xl" mt={2} minH="64px">{newProduct.name || "Your product name"}</Heading>
						<Text fontSize="xl" fontWeight="700" mt={3}>{formatPrice(newProduct.price || 0)}</Text>
					</Box>
				</Box>
			</Grid>

			<Flex justify="space-between" align="flex-end" mb={6} direction={{ base: "column", sm: "row" }} gap={4}>
				<Box>
					<Text fontSize="10px" fontWeight="700" letterSpacing="0.24em" color="velora.accent" mb={2}>CATALOG</Text>
					<Heading fontSize="3xl">Products in the edit</Heading>
				</Box>
				<Button as={RouterLink} to="/" variant="ghost" rightIcon={<FiArrowRight />} color="velora.accent">
					View storefront
				</Button>
			</Flex>
			<SimpleGrid columns={{ base: 1, sm: 2, lg: 3, xl: 4 }} spacing={6}>
				{products.map((product, index) => (
					<ProductCard key={product._id || product.id || index} product={product} index={index} showAdmin />
				))}
			</SimpleGrid>
		</Container>
	);
};

export default CreatePage;
