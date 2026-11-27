import {
	Box,
	Button,
	Container,
	Drawer,
	DrawerBody,
	DrawerCloseButton,
	DrawerContent,
	DrawerHeader,
	DrawerOverlay,
	Flex,
	HStack,
	IconButton,
	Input,
	InputGroup,
	InputLeftElement,
	Text,
	useColorMode,
	useColorModeValue,
	useDisclosure,
	VStack,
} from "@chakra-ui/react";
import { Link as RouterLink, useLocation, useNavigate } from "react-router-dom";
import { FiHeart, FiMenu, FiMoon, FiSearch, FiShoppingBag, FiSun } from "react-icons/fi";
import BrandMark from "./BrandMark";
import { BRAND } from "../brand";
import { useCartStore } from "../store/cart";
import { useShopStore } from "../store/shop";

const navLinks = [
	{ label: "Shop the edit", to: "/#edit" },
	{ label: "Collections", to: "/#collections" },
	{ label: "Saved", to: "/wishlist" },
	{ label: "Studio", to: "/studio" },
];

const Navbar = () => {
	const { colorMode, toggleColorMode } = useColorMode();
	const { isOpen, onOpen, onClose } = useDisclosure();
	const location = useLocation();
	const navigate = useNavigate();

	const search = useShopStore((state) => state.search);
	const setSearch = useShopStore((state) => state.setSearch);
	const cart = useCartStore((state) => state.cart);
	const wishlist = useCartStore((state) => state.wishlist);
	const openCart = useCartStore((state) => state.openCart);

	const cartCount = cart.reduce((total, item) => total + item.quantity, 0);
	const headerBg = useColorModeValue("rgba(250,248,245,0.94)", "rgba(14,15,18,0.94)");
	const borderColor = useColorModeValue("velora.line", "velora.lineDark");
	const muted = useColorModeValue("velora.muted", "velora.mutedDark");

	const handleSearch = (value) => {
		setSearch(value);
		if (location.pathname !== "/") navigate("/");
	};

	return (
		<Box>
			<Box bg="velora.ink" color="whiteAlpha.900" py={2}>
				<Container maxW="1280px" px={{ base: 4, md: 6, lg: 8 }}>
					<Flex justify="space-between" align="center" fontSize="10px" letterSpacing="0.14em" textTransform="uppercase">
						<Text>Complimentary shipping on orders $150+</Text>
						<HStack spacing={6} display={{ base: "none", md: "flex" }}>
							<Text opacity={0.72}>New season, new essentials</Text>
							<Text as="span" opacity={0.45}>|</Text>
							<Text opacity={0.72}>{BRAND.tagline}</Text>
						</HStack>
					</Flex>
				</Container>
			</Box>

			<Box
				position="sticky"
				top={0}
				zIndex={20}
				bg={headerBg}
				backdropFilter="blur(14px)"
				borderBottom="1px solid"
				borderColor={borderColor}
			>
				<Container maxW="1280px" px={{ base: 4, md: 6, lg: 8 }}>
					<Flex h={{ base: 16, md: 20 }} align="center" justify="space-between" gap={4}>
						<HStack as={RouterLink} to="/" spacing={3} flexShrink={0}>
							<BrandMark size={{ base: 8, md: 9 }} />
							<VStack spacing={0} align="flex-start">
								<Text
									fontFamily="heading"
									fontSize={{ base: "xl", md: "2xl" }}
									fontWeight="700"
									letterSpacing="0.16em"
									lineHeight="1.1"
								>
									{BRAND.name}
								</Text>
								<Text fontSize="8px" letterSpacing="0.34em" color={muted}>
									CURATED GOODS
								</Text>
							</VStack>
						</HStack>

						<HStack as="nav" spacing={7} display={{ base: "none", xl: "flex" }}>
							{navLinks.map((link) => (
								<Text
									as={RouterLink}
									to={link.to}
									key={link.label}
									fontSize="sm"
									fontWeight="500"
									color={muted}
									position="relative"
									_hover={{ color: "velora.accent" }}
								>
									{link.label}
								</Text>
							))}
						</HStack>

						<InputGroup maxW="260px" display={{ base: "none", lg: "flex" }}>
							<InputLeftElement pointerEvents="none">
								<FiSearch color={muted} />
							</InputLeftElement>
							<Input
								size="sm"
								value={search}
								onChange={(event) => handleSearch(event.target.value)}
								placeholder="Search the edit"
								bg={useColorModeValue("white", "velora.nightSurface")}
								fontSize="sm"
							/>
						</InputGroup>

						<HStack spacing={1}>
							<IconButton
								aria-label="Toggle color mode"
								variant="ghost"
								icon={colorMode === "light" ? <FiMoon /> : <FiSun />}
								onClick={toggleColorMode}
								borderRadius="full"
								color={muted}
							/>
							<Box position="relative" display={{ base: "none", md: "block" }}>
								<IconButton
									as={RouterLink}
									to="/wishlist"
									aria-label="Saved items"
									variant="ghost"
									icon={<FiHeart />}
									borderRadius="full"
									color={muted}
								/>
								{wishlist.length > 0 && (
									<Box
										position="absolute"
										top={0}
										right={0}
										bg="velora.accent"
										color="white"
										fontSize="9px"
										fontWeight="700"
										w={4}
										h={4}
										borderRadius="full"
										display="grid"
										placeItems="center"
									>
										{wishlist.length}
									</Box>
								)}
							</Box>
							<Button
								variant="outlineInk"
								size="sm"
								leftIcon={<FiShoppingBag />}
								onClick={openCart}
								px={{ base: 3, md: 4 }}
							>
								<Text display={{ base: "none", sm: "inline" }}>Bag</Text>
								<Box as="span" ml={1} color="velora.accent" fontWeight="700">
									({cartCount})
								</Box>
							</Button>
							<IconButton
								aria-label="Open menu"
								variant="ghost"
								icon={<FiMenu />}
								borderRadius="full"
								display={{ base: "inline-flex", xl: "none" }}
								onClick={onOpen}
							/>
						</HStack>
					</Flex>
				</Container>
			</Box>

			<Drawer isOpen={isOpen} onClose={onClose} placement="left" size="sm">
				<DrawerOverlay />
				<DrawerContent bg={useColorModeValue("velora.canvas", "velora.night")}>
					<DrawerCloseButton />
					<DrawerHeader pt={8}>
						<HStack>
							<BrandMark size={8} />
							<Text fontFamily="heading" letterSpacing="0.14em" fontSize="xl">
								{BRAND.name}
							</Text>
						</HStack>
					</DrawerHeader>
					<DrawerBody>
						<InputGroup mb={6}>
							<InputLeftElement pointerEvents="none">
								<FiSearch />
							</InputLeftElement>
							<Input
								value={search}
								onChange={(event) => handleSearch(event.target.value)}
								placeholder="Search the edit"
							/>
						</InputGroup>
						<VStack align="stretch" spacing={1}>
							{navLinks.map((link) => (
								<Text
									as={RouterLink}
									to={link.to}
									key={link.label}
									onClick={onClose}
									py={3}
									borderBottom="1px solid"
									borderColor={borderColor}
									fontFamily="heading"
									fontSize="lg"
									_hover={{ color: "velora.accent" }}
								>
									{link.label}
								</Text>
							))}
							<Button variant="accent" mt={6} onClick={toggleColorMode}>
								{colorMode === "light" ? "Switch to dark mode" : "Switch to light mode"}
							</Button>
						</VStack>
					</DrawerBody>
				</DrawerContent>
			</Drawer>
		</Box>
	);
};

export default Navbar;
