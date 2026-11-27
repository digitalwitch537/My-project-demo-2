import { useEffect, useMemo } from "react";
import {
	Box,
	Button,
	Container,
	Flex,
	Grid,
	Heading,
	HStack,
	Icon,
	Image,
	Input,
	InputGroup,
	InputLeftElement,
	Select,
	SimpleGrid,
	Skeleton,
	Text,
	useColorModeValue,
	VStack,
} from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";
import { FiArrowRight, FiArrowUpRight, FiHome, FiRefreshCw, FiSearch, FiShield, FiStar, FiTruck } from "react-icons/fi";
import ProductCard from "../components/ProductCard";
import { BRAND } from "../brand";
import { useProductStore } from "../store/product";
import { useShopStore } from "../store/shop";
import { CATEGORY_FILTERS, filterProducts } from "../utils/catalog";

const collections = [
	{
		name: "Home & Living",
		caption: "Warm textures, quiet statements",
		gradient: "linear(135deg, #EFE0CC, #C9A87F)",
		icon: FiHome,
		category: "Home",
	},
	{
		name: "Personal Style",
		caption: "The pieces you reach for again",
		gradient: "linear(135deg, #D9DDE3, #9CA8B4)",
		icon: FiStar,
		category: "Style",
	},
	{
		name: "Everyday Tech",
		caption: "Considered tools for modern life",
		gradient: "linear(135deg, #DCE5DF, #8FA99B)",
		icon: FiShield,
		category: "Tech",
	},
];

const promises = [
	{ icon: FiTruck, title: "Complimentary shipping", body: "On every order over $150" },
	{ icon: FiRefreshCw, title: "Easy 30-day returns", body: "No questions, no fuss" },
	{ icon: FiShield, title: "Secure checkout", body: "Your details stay protected" },
];

const HomePage = () => {
	const products = useProductStore((state) => state.products);
	const fetchProducts = useProductStore((state) => state.fetchProducts);
	const isLoading = useProductStore((state) => state.isLoading);

	const search = useShopStore((state) => state.search);
	const category = useShopStore((state) => state.category);
	const sort = useShopStore((state) => state.sort);
	const setSearch = useShopStore((state) => state.setSearch);
	const setCategory = useShopStore((state) => state.setCategory);
	const setSort = useShopStore((state) => state.setSort);
	const resetFilters = useShopStore((state) => state.resetFilters);

	const surface = useColorModeValue("velora.surface", "velora.nightSurface");
	const muted = useColorModeValue("velora.muted", "velora.mutedDark");
	const borderColor = useColorModeValue("velora.line", "velora.lineDark");
	const sectionBg = useColorModeValue("velora.light", "velora.nightSurface");
	const promiseBg = useColorModeValue("velora.accentSoft", "velora.nightSurface");

	useEffect(() => {
		fetchProducts();
	}, [fetchProducts]);

	const visibleProducts = useMemo(
		() => filterProducts(products || [], { search, category, sort }),
		[products, search, category, sort]
	);

	return (
		<Box>
			<Container maxW="1280px" px={{ base: 4, md: 6, lg: 8 }} pt={{ base: 6, md: 10 }}>
				<Box
					position="relative"
					overflow="hidden"
					borderRadius={{ base: "2xl", lg: "3xl" }}
					bg={surface}
					border="1px solid"
					borderColor={borderColor}
				>
					<Grid templateColumns={{ base: "1fr", lg: "1.05fr 0.95fr" }}>
						<VStack
							align="flex-start"
							justify="center"
							spacing={6}
							p={{ base: 8, md: 12, lg: 16 }}
						>
							<HStack spacing={3}>
								<Box w={8} h="2px" bg="velora.accent" />
								<Text fontSize="10px" fontWeight="700" letterSpacing="0.24em" color="velora.accent">
									THE NEW SEASON
								</Text>
							</HStack>
							<Heading
								fontSize={{ base: "4xl", md: "5xl", lg: "6xl" }}
								lineHeight="1.06"
								fontWeight="600"
							>
								Objects of quiet{" "}
								<Text as="span" color="velora.accent" fontStyle="italic">luxury.</Text>
							</Heading>
							<Text color={muted} fontSize={{ base: "sm", md: "md" }} lineHeight="1.9" maxW="480px">
								{BRAND.description} Discover considered essentials designed to stay in rotation for years, not seasons.
							</Text>
							<HStack spacing={{ base: 3, md: 4 }} flexWrap="wrap">
								<Button
									as={RouterLink}
									to="/#edit"
									variant="accent"
									size="lg"
									rightIcon={<FiArrowRight />}
								>
									Shop the edit
								</Button>
								<Button as={RouterLink} to="/#story" variant="outlineInk" size="lg">
									Our story
								</Button>
							</HStack>
							<HStack spacing={{ base: 6, md: 10 }} pt={6}>
								<Box>
									<Text fontFamily="heading" fontSize="2xl" color="velora.accent">40+</Text>
									<Text fontSize="xs" color={muted} letterSpacing="0.06em">CURATED PIECES</Text>
								</Box>
								<Box borderLeft="1px solid" borderColor={borderColor} pl={{ base: 6, md: 10 }}>
									<Text fontFamily="heading" fontSize="2xl" color="velora.accent">30 days</Text>
									<Text fontSize="xs" color={muted} letterSpacing="0.06em">EASY RETURNS</Text>
								</Box>
							</HStack>
						</VStack>

						<Box
							position="relative"
							minH={{ base: "360px", lg: "560px" }}
							bgGradient="linear(145deg, #F1E4D2 0%, #D9B994 46%, #1E1B18 100%)"
							overflow="hidden"
						>
							<Box
								position="absolute"
								top="-80px"
								right="-60px"
								boxSize="320px"
								borderRadius="full"
								border="1px solid"
								borderColor="whiteAlpha.500"
							/>
							<Box
								position="absolute"
								bottom="-100px"
								left="-40px"
								boxSize="360px"
								borderRadius="full"
								border="1px solid"
								borderColor="whiteAlpha.400"
							/>
							<Text
								position="absolute"
								top="-40px"
								left="50%"
								transform="translateX(-50%)"
								fontFamily="heading"
								fontSize="340px"
								lineHeight="1"
								color="whiteAlpha.200"
								userSelect="none"
							>
								V
							</Text>
							<Box
								position="absolute"
								top="22%"
								left="20%"
								w="58%"
								h="60%"
								borderRadius="3xl"
								overflow="hidden"
								boxShadow="2xl"
								transform="rotate(-4deg)"
								bg="whiteAlpha.300"
							>
								{products?.[0]?.image && (
									<Image
										src={products[0].image}
										alt={products[0].name}
										w="full"
										h="full"
										objectFit="cover"
									/>
								)}
							</Box>
							<Box
								position="absolute"
								right={6}
								bottom={6}
								bg="whiteAlpha.900"
								color="velora.ink"
								px={5}
								py={3}
								borderRadius="full"
								boxShadow="lg"
							>
								<Text fontSize="9px" letterSpacing="0.2em" color="velora.accent">NEW ARRIVALS</Text>
								<Text fontFamily="heading" fontSize="sm">Edition 01 / 2026</Text>
							</Box>
						</Box>
					</Grid>
				</Box>
			</Container>

			<Container maxW="1280px" px={{ base: 4, md: 6, lg: 8 }} py={{ base: 10, md: 14 }}>
				<SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
					{promises.map((promise) => (
						<Flex key={promise.title} align="center" gap={4} px={{ base: 2, md: 4 }}>
							<Box
								w={11}
								h={11}
								flexShrink={0}
								borderRadius="full"
								bg={promiseBg}
								color="velora.accent"
								display="grid"
								placeItems="center"
								border="1px solid"
								borderColor={borderColor}
							>
								<Icon as={promise.icon} boxSize={5} />
							</Box>
							<Box>
								<Text fontWeight="700" fontSize="sm">{promise.title}</Text>
								<Text fontSize="xs" color={muted}>{promise.body}</Text>
							</Box>
						</Flex>
					))}
				</SimpleGrid>
			</Container>

			<Box id="collections" bg={sectionBg} py={{ base: 14, md: 20 }}>
				<Container maxW="1280px" px={{ base: 4, md: 6, lg: 8 }}>
					<Flex justify="space-between" align="flex-end" mb={8} gap={6} direction={{ base: "column", md: "row" }}>
						<Box>
							<Text fontSize="10px" fontWeight="700" letterSpacing="0.24em" color="velora.accent" mb={3}>
								EXPLORE BY CATEGORY
							</Text>
							<Heading fontSize={{ base: "3xl", md: "4xl" }}>Collections with a point of view</Heading>
						</Box>
						<Text color={muted} fontSize="sm" maxW="360px">
							Four considered worlds, one simple idea: fewer, better things.
						</Text>
					</Flex>
					<SimpleGrid columns={{ base: 1, md: 3 }} spacing={6}>
						{collections.map((item) => (
							<Box
								key={item.name}
								as={RouterLink}
								to="/#edit"
								position="relative"
								minH="260px"
								borderRadius="2xl"
								overflow="hidden"
								p={7}
								bgGradient={item.gradient}
								color="velora.ink"
								onClick={() => setCategory(item.category)}
								transition="transform 0.3s ease, box-shadow 0.3s ease"
								_hover={{ transform: "translateY(-6px)", shadow: "xl" }}
							>
								<Icon as={item.icon} boxSize={7} mb={10} opacity={0.7} />
								<Heading fontSize="2xl" mt={10}>{item.name}</Heading>
								<Text fontSize="sm" opacity={0.75} mt={2}>{item.caption}</Text>
								<HStack mt={5} spacing={2} fontSize="sm" fontWeight="700">
									<Text>Explore</Text>
									<FiArrowUpRight />
								</HStack>
							</Box>
						))}
					</SimpleGrid>
				</Container>
			</Box>

			<Container maxW="1280px" px={{ base: 4, md: 6, lg: 8 }} py={{ base: 14, md: 20 }} id="edit">
				<Flex justify="space-between" align="flex-end" gap={8} direction={{ base: "column", lg: "row" }} mb={8}>
					<Box>
						<Text fontSize="10px" fontWeight="700" letterSpacing="0.24em" color="velora.accent" mb={3}>
							THE VELORA EDIT
						</Text>
						<Heading fontSize={{ base: "3xl", md: "5xl" }}>Good things, thoughtfully chosen.</Heading>
					</Box>
					<Flex gap={3} w={{ base: "full", lg: "auto" }} direction={{ base: "column", sm: "row" }}>
						<InputGroup maxW={{ base: "full", sm: "280px" }}>
							<InputLeftElement pointerEvents="none"><FiSearch color={muted} /></InputLeftElement>
							<Input
								value={search}
								onChange={(event) => setSearch(event.target.value)}
								placeholder="Search the edit"
								bg={surface}
								fontSize="sm"
							/>
						</InputGroup>
						<Select
							value={sort}
							onChange={(event) => setSort(event.target.value)}
							bg={surface}
							fontSize="sm"
							maxW={{ base: "full", sm: "180px" }}
						>
							<option value="featured">Featured</option>
							<option value="price-asc">Price: low to high</option>
							<option value="price-desc">Price: high to low</option>
							<option value="name">Name: A–Z</option>
						</Select>
					</Flex>
				</Flex>

				<HStack spacing={2} mb={10} overflowX="auto" pb={2}>
					{CATEGORY_FILTERS.map((item) => (
						<Button
							key={item}
							size="sm"
							flexShrink={0}
							variant={category === item ? "brand" : "outlineInk"}
							onClick={() => setCategory(item)}
						>
							{item}
						</Button>
					))}
				</HStack>

				{isLoading ? (
					<SimpleGrid columns={{ base: 1, sm: 2, lg: 3, xl: 4 }} spacing={6}>
						{Array.from({ length: 4 }).map((_, index) => (
							<Box key={index} borderRadius="2xl" overflow="hidden" border="1px solid" borderColor={borderColor}>
								<Skeleton h="280px" />
								<VStack align="stretch" p={5} spacing={3}>
									<Skeleton h={3} w="40%" />
									<Skeleton h={5} w="80%" />
									<Skeleton h={5} w="30%" />
								</VStack>
							</Box>
						))}
					</SimpleGrid>
				) : visibleProducts.length > 0 ? (
					<SimpleGrid columns={{ base: 1, sm: 2, lg: 3, xl: 4 }} spacing={6}>
						{visibleProducts.map((product, index) => (
							<ProductCard key={product._id || product.id || index} product={product} index={index} />
						))}
					</SimpleGrid>
				) : (
					<VStack
						spacing={5}
						py={20}
						border="1px dashed"
						borderColor={borderColor}
						borderRadius="2xl"
						textAlign="center"
					>
						<Text fontFamily="heading" fontSize="3xl">
							{products?.length ? "Nothing matches that search" : "The edit is being curated"}
						</Text>
						<Text color={muted} fontSize="sm" maxW="420px">
							{products?.length
								? "Try another category or clear your filters to see everything in the collection."
								: "New pieces are on their way. Check back shortly or add the first piece in the studio."}
						</Text>
						<HStack spacing={3}>
							{products?.length > 0 && (
								<Button variant="outlineInk" onClick={resetFilters}>Clear filters</Button>
							)}
							<Button as={RouterLink} to="/studio" variant="accent" rightIcon={<FiArrowRight />}>
								Visit the studio
							</Button>
						</HStack>
					</VStack>
				)}
			</Container>

			<Container maxW="1280px" px={{ base: 4, md: 6, lg: 8 }} pb={{ base: 14, md: 20 }} id="story">
				<Box
					position="relative"
					overflow="hidden"
					borderRadius="3xl"
					bg="velora.ink"
					color="velora.light"
				>
					<Grid templateColumns={{ base: "1fr", lg: "1.1fr 0.9fr" }}>
						<VStack align="flex-start" spacing={6} p={{ base: 8, md: 12, lg: 16 }}>
							<Text fontSize="10px" fontWeight="700" letterSpacing="0.24em" color="velora.accentLight">
								OUR PHILOSOPHY
							</Text>
							<Heading fontSize={{ base: "3xl", md: "5xl" }} lineHeight="1.12" maxW="560px">
								Made for the moments in between.
							</Heading>
							<Text color="whiteAlpha.700" fontSize="sm" lineHeight="1.9" maxW="480px">
								We believe the best things are the ones you use every day. That&apos;s why every piece in the {BRAND.name} edit is chosen for its quiet detail, honest materials, and the way it makes an ordinary moment feel a little more special.
							</Text>
							<Button
								as={RouterLink}
								to="/#edit"
								variant="accent"
								rightIcon={<FiArrowRight />}
							>
								Explore the collection
							</Button>
						</VStack>
						<Box
							position="relative"
							minH={{ base: "300px", lg: "440px" }}
							bgGradient="linear(160deg, #2A231C, #B2763F)"
							display="grid"
							placeItems="center"
							p={10}
						>
							<Box
								position="absolute"
								inset={6}
								border="1px solid"
								borderColor="whiteAlpha.300"
								borderRadius="2xl"
							/>
							<VStack spacing={4} textAlign="center" position="relative">
								<Text fontFamily="heading" fontSize={{ base: "3xl", md: "4xl" }} fontStyle="italic">
									&ldquo;Buy less. Choose well.&rdquo;
								</Text>
								<Text fontSize="10px" letterSpacing="0.2em" color="whiteAlpha.700">
									THE VELORA PROMISE
								</Text>
							</VStack>
						</Box>
					</Grid>
				</Box>
			</Container>
		</Box>
	);
};

export default HomePage;
