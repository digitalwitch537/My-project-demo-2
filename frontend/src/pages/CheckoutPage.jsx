import { useState } from "react";
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
	Input,
	Text,
	useColorModeValue,
	VStack,
} from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";
import { FiArrowLeft, FiArrowRight, FiCheck, FiLock, FiShoppingBag } from "react-icons/fi";
import { formatPrice } from "../utils/catalog";
import { useCartStore } from "../store/cart";

const CheckoutPage = () => {
	const [placed, setPlaced] = useState(false);
	const [order, setOrder] = useState({ number: "", total: 0 });

	const cart = useCartStore((state) => state.cart);
	const clearCart = useCartStore((state) => state.clearCart);

	const surface = useColorModeValue("velora.surface", "velora.nightSurface");
	const muted = useColorModeValue("velora.muted", "velora.mutedDark");
	const borderColor = useColorModeValue("velora.line", "velora.lineDark");

	const subtotal = cart.reduce((total, item) => total + Number(item.price) * item.quantity, 0);
	const shipping = subtotal >= 150 ? 0 : 12;
	const tax = subtotal * 0.08;
	const total = subtotal + shipping + tax;

	const handleSubmit = (event) => {
		event.preventDefault();
		setOrder({ number: `VL-${String(Date.now()).slice(-6)}`, total });
		clearCart();
		setPlaced(true);
	};

	if (placed) {
		return (
			<Container maxW="container.md" px={{ base: 4, md: 6 }} py={{ base: 20, md: 32 }}>
				<VStack spacing={7} textAlign="center">
					<Box w={24} h={24} borderRadius="full" bg="velora.accentSoft" color="velora.accent" display="grid" placeItems="center" fontSize="4xl">
						<FiCheck />
					</Box>
					<Heading fontSize={{ base: "4xl", md: "5xl" }}>Thank you for your order.</Heading>
					<Text color={muted} fontSize="sm" lineHeight="1.9" maxW="480px">
						Your VELORA pieces are on their way. A confirmation for order{" "}
						<Text as="span" fontWeight="700">{order.number}</Text> has been sent to your email.
					</Text>
					<HStack spacing={6} fontSize="sm" color={muted}>
						<Text>Order total: <Text as="span" fontWeight="700">{formatPrice(order.total)}</Text></Text>
						<Text>Estimated delivery: 3–5 days</Text>
					</HStack>
					<Button as={RouterLink} to="/" variant="accent" size="lg" rightIcon={<FiArrowRight />}>
						Back to the edit
					</Button>
					<Text fontSize="10px" letterSpacing="0.12em" textTransform="uppercase" color={muted}>
						Demo checkout — no payment was processed
					</Text>
				</VStack>
			</Container>
		);
	}

	if (cart.length === 0) {
		return (
			<Container maxW="container.md" px={{ base: 4, md: 6 }} py={{ base: 20, md: 32 }}>
				<VStack spacing={6} textAlign="center">
					<Box w={24} h={24} borderRadius="full" bg="velora.accentSoft" color="velora.accent" display="grid" placeItems="center" fontSize="4xl">
						<FiShoppingBag />
					</Box>
					<Heading fontSize={{ base: "4xl", md: "5xl" }}>Nothing to check out yet</Heading>
					<Text color={muted} fontSize="sm">Add a few pieces to your bag first.</Text>
					<Button as={RouterLink} to="/#edit" variant="accent" rightIcon={<FiArrowRight />}>
						Shop the edit
					</Button>
				</VStack>
			</Container>
		);
	}

	return (
		<Container maxW="1280px" px={{ base: 4, md: 6, lg: 8 }} py={{ base: 10, md: 16 }}>
			<VStack align="flex-start" spacing={2} mb={10}>
				<Text as={RouterLink} to="/cart" fontSize="xs" color={muted} _hover={{ color: "velora.accent" }}>
					<FiArrowLeft style={{ display: "inline", marginRight: 6 }} /> Back to bag
				</Text>
				<Heading fontSize={{ base: "4xl", md: "5xl" }}>Checkout</Heading>
				<HStack spacing={2} fontSize="xs" color={muted}>
					<FiLock />
					<Text>Secure demo checkout — no payment is processed</Text>
				</HStack>
			</VStack>

			<Grid templateColumns={{ base: "1fr", lg: "1.2fr 0.8fr" }} gap={8} alignItems="start">
				<Box
					as="form"
					onSubmit={handleSubmit}
					p={{ base: 6, md: 8 }}
					bg={surface}
					border="1px solid"
					borderColor={borderColor}
					borderRadius="2xl"
				>
					<VStack align="stretch" spacing={7}>
						<Box>
							<Heading fontSize="2xl" mb={5}>Contact</Heading>
							<FormControl isRequired>
								<FormLabel fontSize="xs" textTransform="uppercase" letterSpacing="0.08em" color={muted}>Email address</FormLabel>
								<Input type="email" placeholder="you@example.com" />
							</FormControl>
						</Box>
						<Box>
							<Heading fontSize="2xl" mb={5}>Delivery details</Heading>
							<VStack align="stretch" spacing={4}>
								<FormControl isRequired>
									<FormLabel fontSize="xs" textTransform="uppercase" letterSpacing="0.08em" color={muted}>Full name</FormLabel>
									<Input placeholder="Jane Doe" />
								</FormControl>
								<FormControl isRequired>
									<FormLabel fontSize="xs" textTransform="uppercase" letterSpacing="0.08em" color={muted}>Address</FormLabel>
									<Input placeholder="123 Market Street" />
								</FormControl>
								<Grid templateColumns={{ base: "1fr", sm: "1fr 1fr" }} gap={4}>
									<FormControl isRequired>
										<FormLabel fontSize="xs" textTransform="uppercase" letterSpacing="0.08em" color={muted}>City</FormLabel>
										<Input placeholder="New York" />
									</FormControl>
									<FormControl isRequired>
										<FormLabel fontSize="xs" textTransform="uppercase" letterSpacing="0.08em" color={muted}>Postal code</FormLabel>
										<Input placeholder="10001" />
									</FormControl>
								</Grid>
							</VStack>
						</Box>
						<Box>
							<Heading fontSize="2xl" mb={5}>Payment</Heading>
							<VStack align="stretch" spacing={4}>
								<FormControl isRequired>
									<FormLabel fontSize="xs" textTransform="uppercase" letterSpacing="0.08em" color={muted}>Card number</FormLabel>
									<Input inputMode="numeric" placeholder="4242 4242 4242 4242" />
								</FormControl>
								<Grid templateColumns="1fr 1fr" gap={4}>
									<FormControl isRequired>
										<FormLabel fontSize="xs" textTransform="uppercase" letterSpacing="0.08em" color={muted}>Expiry</FormLabel>
										<Input placeholder="MM / YY" />
									</FormControl>
									<FormControl isRequired>
										<FormLabel fontSize="xs" textTransform="uppercase" letterSpacing="0.08em" color={muted}>CVC</FormLabel>
										<Input inputMode="numeric" placeholder="123" />
									</FormControl>
								</Grid>
							</VStack>
						</Box>
						<Button type="submit" variant="accent" size="lg" w="full" rightIcon={<FiArrowRight />}>
							Place order
						</Button>
					</VStack>
				</Box>

				<Box
					p={7}
					bg={surface}
					border="1px solid"
					borderColor={borderColor}
					borderRadius="2xl"
				>
					<Heading fontSize="2xl" mb={6}>Your order</Heading>
					<VStack align="stretch" spacing={4} mb={6}>
						{cart.map((item) => (
							<Flex key={item._id || item.id} justify="space-between" gap={4} fontSize="sm">
								<Text flex={1} noOfLines={1}>{item.name} × {item.quantity}</Text>
								<Text fontWeight="600">{formatPrice(Number(item.price) * item.quantity)}</Text>
							</Flex>
						))}
					</VStack>
					<VStack align="stretch" spacing={3} fontSize="sm" borderTop="1px solid" borderColor={borderColor} pt={5}>
						<Flex justify="space-between"><Text color={muted}>Subtotal</Text><Text>{formatPrice(subtotal)}</Text></Flex>
						<Flex justify="space-between"><Text color={muted}>Shipping</Text><Text>{shipping === 0 ? "Complimentary" : formatPrice(shipping)}</Text></Flex>
						<Flex justify="space-between"><Text color={muted}>Estimated tax</Text><Text>{formatPrice(tax)}</Text></Flex>
						<Flex justify="space-between" align="baseline" pt={3} borderTop="1px solid" borderColor={borderColor}>
							<Text fontWeight="700">Total</Text>
							<Text fontFamily="heading" fontSize="3xl" color="velora.accent">{formatPrice(total)}</Text>
						</Flex>
					</VStack>
				</Box>
			</Grid>
		</Container>
	);
};

export default CheckoutPage;
