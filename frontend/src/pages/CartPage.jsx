import { useState } from "react";
import {
	Box,
	Button,
	Container,
	Divider,
	Flex,
	Grid,
	Heading,
	HStack,
	IconButton,
	Image,
	Input,
	InputGroup,
	InputRightElement,
	Text,
	useColorModeValue,
	VStack,
} from "@chakra-ui/react";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import { FiArrowLeft, FiArrowRight, FiMinus, FiPlus, FiShoppingBag, FiTrash2 } from "react-icons/fi";
import { formatPrice } from "../utils/catalog";
import { useCartStore } from "../store/cart";

const CartPage = () => {
	const navigate = useNavigate();
	const [promo, setPromo] = useState("");
	const [discountApplied, setDiscountApplied] = useState(false);

	const cart = useCartStore((state) => state.cart);
	const updateQuantity = useCartStore((state) => state.updateQuantity);
	const removeFromCart = useCartStore((state) => state.removeFromCart);

	const surface = useColorModeValue("velora.surface", "velora.nightSurface");
	const muted = useColorModeValue("velora.muted", "velora.mutedDark");
	const borderColor = useColorModeValue("velora.line", "velora.lineDark");

	const subtotal = cart.reduce((total, item) => total + Number(item.price) * item.quantity, 0);
	const discount = discountApplied ? subtotal * 0.1 : 0;
	const shipping = subtotal >= 150 ? 0 : 12;
	const tax = (subtotal - discount) * 0.08;
	const total = subtotal - discount + shipping + tax;

	const handlePromo = () => {
		if (promo.trim().toUpperCase() === "VELORA10") setDiscountApplied(true);
	};

	if (cart.length === 0) {
		return (
			<Container maxW="1280px" px={{ base: 4, md: 6, lg: 8 }} py={{ base: 16, md: 28 }}>
				<VStack spacing={6} textAlign="center">
					<Box w={24} h={24} borderRadius="full" bg="velora.accentSoft" color="velora.accent" display="grid" placeItems="center" fontSize="4xl">
						<FiShoppingBag />
					</Box>
					<Heading fontSize={{ base: "4xl", md: "5xl" }}>Your bag is empty</Heading>
					<Text color={muted} maxW="440px" fontSize="sm" lineHeight="1.9">
						The best things are worth choosing slowly. Explore the edit and find something that stays with you.
					</Text>
					<Button as={RouterLink} to="/#edit" variant="accent" size="lg" rightIcon={<FiArrowRight />}>
						Explore the edit
					</Button>
				</VStack>
			</Container>
		);
	}

	return (
		<Container maxW="1280px" px={{ base: 4, md: 6, lg: 8 }} py={{ base: 10, md: 16 }}>
			<VStack align="flex-start" spacing={2} mb={10}>
				<Text as={RouterLink} to="/" fontSize="xs" color={muted} _hover={{ color: "velora.accent" }}>
					<FiArrowLeft style={{ display: "inline", marginRight: 6 }} /> Continue shopping
				</Text>
				<Heading fontSize={{ base: "4xl", md: "5xl" }}>Your bag</Heading>
				<Text color={muted} fontSize="sm">{cart.length} {cart.length === 1 ? "piece" : "pieces"} in your selection</Text>
			</VStack>

			<Grid templateColumns={{ base: "1fr", lg: "1.5fr 0.75fr" }} gap={8} alignItems="start">
				<Box>
					<VStack align="stretch" spacing={4}>
						{cart.map((item) => (
							<Flex
								key={item._id || item.id}
								gap={5}
								p={4}
								bg={surface}
								border="1px solid"
								borderColor={borderColor}
								borderRadius="2xl"
								direction={{ base: "column", sm: "row" }}
							>
								<Box
									boxSize={{ base: "full", sm: "140px" }}
									h={{ base: "240px", sm: "140px" }}
									flexShrink={0}
									borderRadius="xl"
									overflow="hidden"
									bg="velora.accentSoft"
								>
									<Image src={item.image} alt={item.name} w="full" h="full" objectFit="cover" />
								</Box>
								<Flex flex={1} justify="space-between" direction={{ base: "column", md: "row" }} gap={4}>
									<Box>
										<Text fontFamily="heading" fontSize="xl">{item.name}</Text>
										<Text fontSize="xs" color={muted} mt={1}>VELORA Edit · Complimentary returns</Text>
										<Text fontSize="lg" fontWeight="700" color="velora.accent" mt={3}>
											{formatPrice(item.price)}
										</Text>
									</Box>
									<HStack spacing={3} align="flex-start">
										<HStack border="1px solid" borderColor={borderColor} borderRadius="full" py={1}>
											<IconButton
												aria-label="Decrease quantity"
												variant="ghost"
												size="sm"
												borderRadius="full"
												icon={<FiMinus />}
												onClick={() => updateQuantity(item._id || item.id, item.quantity - 1)}
											/>
											<Text minW="24px" textAlign="center" fontSize="sm" fontWeight="600">{item.quantity}</Text>
											<IconButton
												aria-label="Increase quantity"
												variant="ghost"
												size="sm"
												borderRadius="full"
												icon={<FiPlus />}
												onClick={() => updateQuantity(item._id || item.id, item.quantity + 1)}
											/>
										</HStack>
										<IconButton
											aria-label="Remove item"
											variant="ghost"
											size="sm"
											color={muted}
											icon={<FiTrash2 />}
											onClick={() => removeFromCart(item._id || item.id)}
										/>
									</HStack>
								</Flex>
							</Flex>
						))}
					</VStack>
				</Box>

				<Box
					alignSelf="start"
					p={7}
					bg={surface}
					border="1px solid"
					borderColor={borderColor}
					borderRadius="2xl"
					position="sticky"
					top="120px"
				>
					<Heading fontSize="2xl" mb={6}>Order summary</Heading>
					<VStack align="stretch" spacing={3} fontSize="sm">
						<Flex justify="space-between"><Text color={muted}>Subtotal</Text><Text>{formatPrice(subtotal)}</Text></Flex>
						{discountApplied && (
							<Flex justify="space-between" color="velora.accent">
								<Text>VELORA10 discount</Text><Text>-{formatPrice(discount)}</Text>
							</Flex>
						)}
						<Flex justify="space-between"><Text color={muted}>Shipping</Text><Text>{shipping === 0 ? "Complimentary" : formatPrice(shipping)}</Text></Flex>
						<Flex justify="space-between"><Text color={muted}>Estimated tax</Text><Text>{formatPrice(tax)}</Text></Flex>
						<Divider borderColor={borderColor} my={2} />
						<Flex justify="space-between" align="baseline">
							<Text fontWeight="700">Total</Text>
							<Text fontFamily="heading" fontSize="3xl" color="velora.accent">{formatPrice(total)}</Text>
						</Flex>
					</VStack>

					<Box mt={7}>
						<Text fontSize="xs" fontWeight="700" letterSpacing="0.08em" textTransform="uppercase" color={muted} mb={2}>
							Promo code
						</Text>
						<InputGroup>
							<Input
								value={promo}
								onChange={(event) => setPromo(event.target.value)}
								placeholder="Enter code"
								fontSize="sm"
							/>
							<InputRightElement w="auto" pr={1}>
								<Button size="sm" variant="outlineInk" onClick={handlePromo} disabled={discountApplied}>
									{discountApplied ? "Applied" : "Apply"}
								</Button>
							</InputRightElement>
						</InputGroup>
						<Text fontSize="10px" color={muted} mt={2}>Try VELORA10 for 10% off.</Text>
					</Box>

					<Button
						variant="accent"
						size="lg"
						w="full"
						mt={7}
						rightIcon={<FiArrowRight />}
						onClick={() => navigate("/checkout")}
					>
						Checkout
					</Button>
					<Text fontSize="xs" color={muted} textAlign="center" mt={4}>
						Secure checkout · Easy 30-day returns
					</Text>
				</Box>
			</Grid>
		</Container>
	);
};

export default CartPage;
