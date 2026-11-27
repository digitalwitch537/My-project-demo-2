import {
	Box,
	Button,
	Drawer,
	DrawerBody,
	DrawerCloseButton,
	DrawerContent,
	DrawerFooter,
	DrawerHeader,
	DrawerOverlay,
	Flex,
	HStack,
	IconButton,
	Image,
	Text,
	useColorModeValue,
	VStack,
} from "@chakra-ui/react";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import { FiArrowRight, FiMinus, FiPlus, FiShoppingBag, FiTrash2 } from "react-icons/fi";
import { formatPrice } from "../utils/catalog";
import { useCartStore } from "../store/cart";

const CartDrawer = () => {
	const navigate = useNavigate();
	const isCartOpen = useCartStore((state) => state.isCartOpen);
	const closeCart = useCartStore((state) => state.closeCart);
	const cart = useCartStore((state) => state.cart);
	const updateQuantity = useCartStore((state) => state.updateQuantity);
	const removeFromCart = useCartStore((state) => state.removeFromCart);

	const surface = useColorModeValue("velora.surface", "velora.nightSurface");
	const muted = useColorModeValue("velora.muted", "velora.mutedDark");
	const borderColor = useColorModeValue("velora.line", "velora.lineDark");
	const subtotal = cart.reduce((total, item) => total + Number(item.price) * item.quantity, 0);
	const count = cart.reduce((total, item) => total + item.quantity, 0);

	const handleCheckout = () => {
		closeCart();
		navigate("/checkout");
	};

	return (
		<Drawer isOpen={isCartOpen} onClose={closeCart} placement="right" size="md">
			<DrawerOverlay bg="blackAlpha.600" backdropFilter="blur(3px)" />
			<DrawerContent bg={surface}>
				<DrawerCloseButton mt={2} />
				<DrawerHeader borderBottom="1px solid" borderColor={borderColor} py={6}>
					<Text fontFamily="heading" fontSize="2xl">
						Your bag
					</Text>
					<Text fontSize="xs" color={muted} fontWeight="500" letterSpacing="0.08em" textTransform="uppercase">
						{count} {count === 1 ? "item" : "items"}
					</Text>
				</DrawerHeader>

				<DrawerBody py={6}>
					{cart.length === 0 ? (
						<VStack h="full" spacing={5} justify="center" textAlign="center" pb={16}>
							<Box
								w={20}
								h={20}
								borderRadius="full"
								bg="velora.accentSoft"
								color="velora.accent"
								display="grid"
								placeItems="center"
								fontSize="3xl"
							>
								<FiShoppingBag />
							</Box>
							<Text fontFamily="heading" fontSize="2xl">Your bag is waiting</Text>
							<Text color={muted} fontSize="sm" maxW="260px">
								Discover the pieces that make everyday feel a little more considered.
							</Text>
							<Button variant="accent" rightIcon={<FiArrowRight />} onClick={closeCart} as={RouterLink} to="/#edit">
								Explore the edit
							</Button>
						</VStack>
					) : (
						<VStack align="stretch" spacing={5}>
							{cart.map((item) => (
								<Flex key={item._id || item.id} gap={4} align="flex-start">
									<Box
										boxSize="88px"
										flexShrink={0}
										borderRadius="xl"
										overflow="hidden"
										bg="velora.accentSoft"
									>
										<Image src={item.image} alt={item.name} boxSize="full" objectFit="cover" />
									</Box>
									<Box flex={1} minW={0}>
										<Flex justify="space-between" gap={2}>
											<Text fontWeight="600" fontSize="sm" noOfLines={2}>{item.name}</Text>
											<IconButton
												aria-label="Remove item"
												size="xs"
												variant="ghost"
												color={muted}
												icon={<FiTrash2 />}
												onClick={() => removeFromCart(item._id || item.id)}
											/>
										</Flex>
										<Text fontSize="sm" color="velora.accent" fontWeight="700" mt={1}>
											{formatPrice(item.price)}
										</Text>
										<HStack
											mt={3}
											border="1px solid"
											borderColor={borderColor}
											borderRadius="full"
											w="fit-content"
										>
											<IconButton
												aria-label="Decrease quantity"
												size="xs"
												variant="ghost"
												borderRadius="full"
												icon={<FiMinus />}
												onClick={() => updateQuantity(item._id || item.id, item.quantity - 1)}
											/>
											<Text fontSize="sm" fontWeight="600" minW="20px" textAlign="center">{item.quantity}</Text>
											<IconButton
												aria-label="Increase quantity"
												size="xs"
												variant="ghost"
												borderRadius="full"
												icon={<FiPlus />}
												onClick={() => updateQuantity(item._id || item.id, item.quantity + 1)}
											/>
										</HStack>
									</Box>
								</Flex>
							))}
						</VStack>
					)}
				</DrawerBody>

				{cart.length > 0 && (
					<DrawerFooter borderTop="1px solid" borderColor={borderColor} py={6} display="block">
						<Flex justify="space-between" mb={1} fontSize="sm" color={muted}>
							<Text>Subtotal</Text>
							<Text>{formatPrice(subtotal)}</Text>
						</Flex>
						<Text fontSize="xs" color={muted} mb={4}>
							Shipping and taxes calculated at checkout.
						</Text>
						<Button variant="accent" w="full" size="lg" onClick={handleCheckout} rightIcon={<FiArrowRight />}>
							Continue to checkout
						</Button>
					</DrawerFooter>
				)}
			</DrawerContent>
		</Drawer>
	);
};

export default CartDrawer;
