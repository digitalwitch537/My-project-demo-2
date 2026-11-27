import { useState } from "react";
import {
	Badge,
	Box,
	Button,
	Flex,
	Grid,
	Heading,
	HStack,
	IconButton,
	Image,
	Input,
	Modal,
	ModalBody,
	ModalCloseButton,
	ModalContent,
	ModalFooter,
	ModalHeader,
	ModalOverlay,
	Text,
	useColorModeValue,
	useDisclosure,
	useToast,
	VStack,
} from "@chakra-ui/react";
import { FiArrowRight, FiEdit2, FiHeart, FiMinus, FiPlus, FiShoppingBag, FiTrash2 } from "react-icons/fi";
import { formatPrice, getProductCategory } from "../utils/catalog";
import { useCartStore } from "../store/cart";
import { useProductStore } from "../store/product";

const ProductCard = ({ product, index = 0, showAdmin = false }) => {
	const [imageFailed, setImageFailed] = useState(false);
	const [quantity, setQuantity] = useState(1);
	const [updatedProduct, setUpdatedProduct] = useState(product);
	const quickView = useDisclosure();
	const editView = useDisclosure();
	const toast = useToast();

	const addToCart = useCartStore((state) => state.addToCart);
	const toggleWishlist = useCartStore((state) => state.toggleWishlist);
	const wishlist = useCartStore((state) => state.wishlist);
	const deleteProduct = useProductStore((state) => state.deleteProduct);
	const updateProduct = useProductStore((state) => state.updateProduct);

	const surface = useColorModeValue("velora.surface", "velora.nightSurface");
	const text = useColorModeValue("velora.ink", "velora.light");
	const muted = useColorModeValue("velora.muted", "velora.mutedDark");
	const borderColor = useColorModeValue("velora.line", "velora.lineDark");

	const id = product._id || product.id;
	const isSaved = wishlist.some((item) => (item._id || item.id) === id);
	const category = getProductCategory(product, index);

	const showToast = (title, description, status) =>
		toast({ title, description, status, duration: 2500, isClosable: true });

	const handleDelete = async () => {
		const { success, message } = await deleteProduct(id);
		showToast(success ? "Product removed" : "Something went wrong", message, success ? "success" : "error");
	};

	const handleUpdate = async () => {
		const { success, message } = await updateProduct(id, updatedProduct);
		editView.onClose();
		showToast(
			success ? "Product updated" : "Something went wrong",
			success ? "Your changes are live in the store." : message,
			success ? "success" : "error"
		);
	};

	const handleAddToCart = () => {
		addToCart(product, quantity);
		quickView.onClose();
		setQuantity(1);
		showToast("Added to your bag", `${product.name} is ready for checkout.`, "success");
	};

	return (
		<Box
			role="group"
			position="relative"
			bg={surface}
			color={text}
			border="1px solid"
			borderColor={borderColor}
			borderRadius="2xl"
			overflow="hidden"
			transition="all 0.3s ease"
			_hover={{
				transform: "translateY(-6px)",
				shadow: "xl",
				borderColor: "velora.accentLight",
			}}
		>
			<Box
				position="relative"
				h={{ base: "260px", md: "280px" }}
				bgGradient="linear(135deg, velora.accentSoft, velora.line)"
				overflow="hidden"
			>
				{!imageFailed && (
					<Image
						src={product.image}
						alt={product.name}
						w="full"
						h="full"
						objectFit="cover"
						loading="lazy"
						transition="transform 0.5s ease"
						_groupHover={{ transform: "scale(1.05)" }}
						onError={() => setImageFailed(true)}
					/>
				)}

				{index < 3 && (
					<Badge
						position="absolute"
						top={4}
						left={4}
						bg="velora.ink"
						color="white"
						fontSize="9px"
						letterSpacing="0.16em"
						px={2.5}
						py={1}
						borderRadius="full"
						textTransform="uppercase"
					>
						New
					</Badge>
				)}

				<IconButton
					aria-label={isSaved ? "Remove from saved" : "Save item"}
					position="absolute"
					top={3}
					right={3}
					size="sm"
					borderRadius="full"
					bg={useColorModeValue("whiteAlpha.900", "blackAlpha.700")}
					color={isSaved ? "velora.accent" : "velora.ink"}
					icon={<FiHeart fill={isSaved ? "currentColor" : "none"} />}
					onClick={() => toggleWishlist(product)}
					_hover={{ bg: "white", color: "velora.accent" }}
				/>

				{showAdmin && (
					<HStack position="absolute" bottom={3} left={3} spacing={1}>
						<IconButton
							aria-label="Edit product"
							size="sm"
							borderRadius="full"
							bg="whiteAlpha.900"
							color="velora.ink"
							icon={<FiEdit2 />}
							onClick={() => {
								setUpdatedProduct(product);
								editView.onOpen();
							}}
						/>
						<IconButton
							aria-label="Delete product"
							size="sm"
							borderRadius="full"
							bg="whiteAlpha.900"
							color="#B43B3B"
							icon={<FiTrash2 />}
							onClick={handleDelete}
						/>
					</HStack>
				)}

				{!showAdmin && (
					<Button
						variant="accent"
						size="sm"
						position="absolute"
						bottom={4}
						left="50%"
						transform="translate(-50%, 12px)"
						opacity={0}
						whiteSpace="nowrap"
						leftIcon={<FiShoppingBag />}
						_groupHover={{ opacity: 1, transform: "translate(-50%, 0)" }}
						_focusVisible={{ opacity: 1, transform: "translate(-50%, 0)" }}
						onClick={quickView.onOpen}
					>
						Quick add
					</Button>
				)}
			</Box>

			<Box p={5}>
				<Text fontSize="10px" fontWeight="700" letterSpacing="0.18em" textTransform="uppercase" color="velora.accent">
					{category}
				</Text>
				<Heading as="h3" fontSize="lg" fontWeight="600" noOfLines={2} mt={2} minH="52px">
					{product.name}
				</Heading>
				<Flex justify="space-between" align="center" mt={4}>
					<Text fontSize="xl" fontWeight="700">{formatPrice(product.price)}</Text>
					{!showAdmin && (
						<Button
							variant="ghost"
							size="sm"
							color="velora.accent"
							rightIcon={<FiArrowRight />}
							onClick={quickView.onOpen}
							px={2}
						>
							View
						</Button>
					)}
				</Flex>
			</Box>

			<Modal isOpen={quickView.isOpen} onClose={quickView.onClose} size="2xl" isCentered>
				<ModalOverlay bg="blackAlpha.700" backdropFilter="blur(4px)" />
				<ModalContent bg={surface} color={text} mx={4} borderRadius="2xl" overflow="hidden">
					<ModalCloseButton zIndex={2} bg={surface} borderRadius="full" m={3} />
					<ModalBody p={0}>
						<Grid templateColumns={{ base: "1fr", md: "1fr 1fr" }}>
							<Box
								h={{ base: "280px", md: "480px" }}
								bgGradient="linear(135deg, velora.accentSoft, velora.line)"
							>
								{!imageFailed && (
									<Image src={product.image} alt={product.name} w="full" h="full" objectFit="cover" />
								)}
							</Box>
							<VStack align="flex-start" spacing={4} p={{ base: 6, md: 10 }}>
								<Text fontSize="10px" fontWeight="700" letterSpacing="0.2em" textTransform="uppercase" color="velora.accent">
									{category} · VELORA Edit
								</Text>
								<Heading fontSize={{ base: "3xl", md: "4xl" }} lineHeight="1.15">
									{product.name}
								</Heading>
								<Text color={muted} fontSize="sm" lineHeight="1.8">
									{product.description ||
										"A considered piece from the VELORA edit — made to bring a little more intention to the everyday."}
								</Text>
								<Text fontSize="2xl" fontWeight="700">{formatPrice(product.price)}</Text>
								<HStack
									border="1px solid"
									borderColor={borderColor}
									borderRadius="full"
									py={1}
								>
									<IconButton
										aria-label="Decrease quantity"
										variant="ghost"
										borderRadius="full"
										size="sm"
										icon={<FiMinus />}
										onClick={() => setQuantity(Math.max(1, quantity - 1))}
									/>
									<Text minW="24px" textAlign="center" fontWeight="600">{quantity}</Text>
									<IconButton
										aria-label="Increase quantity"
										variant="ghost"
										borderRadius="full"
										size="sm"
										icon={<FiPlus />}
										onClick={() => setQuantity(quantity + 1)}
									/>
								</HStack>
								<Button
									variant="accent"
									size="lg"
									w="full"
									leftIcon={<FiShoppingBag />}
									onClick={handleAddToCart}
								>
									Add to bag
								</Button>
								<Button
									variant="outlineInk"
									w="full"
									leftIcon={<FiHeart fill={isSaved ? "currentColor" : "none"} />}
									onClick={() => toggleWishlist(product)}
								>
									{isSaved ? "Saved to your list" : "Save for later"}
								</Button>
								<Text fontSize="xs" color={muted}>
									Complimentary shipping on orders $150+ · Easy 30-day returns
								</Text>
							</VStack>
						</Grid>
					</ModalBody>
				</ModalContent>
			</Modal>

			<Modal isOpen={editView.isOpen} onClose={editView.onClose} isCentered>
				<ModalOverlay />
				<ModalContent bg={surface} color={text}>
					<ModalHeader fontFamily="heading">Edit product</ModalHeader>
					<ModalCloseButton />
					<ModalBody>
						<VStack spacing={4}>
							<Input
								value={updatedProduct.name}
								onChange={(event) => setUpdatedProduct({ ...updatedProduct, name: event.target.value })}
								placeholder="Product name"
							/>
							<Input
								type="number"
								value={updatedProduct.price}
								onChange={(event) => setUpdatedProduct({ ...updatedProduct, price: event.target.value })}
								placeholder="Price"
							/>
							<Input
								value={updatedProduct.image}
								onChange={(event) => setUpdatedProduct({ ...updatedProduct, image: event.target.value })}
								placeholder="Image URL"
							/>
						</VStack>
					</ModalBody>
					<ModalFooter gap={2}>
						<Button variant="ghost" onClick={editView.onClose}>Cancel</Button>
						<Button variant="accent" onClick={handleUpdate}>Save changes</Button>
					</ModalFooter>
				</ModalContent>
			</Modal>
		</Box>
	);
};

export default ProductCard;
