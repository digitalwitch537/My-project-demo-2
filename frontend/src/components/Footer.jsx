import {
	Box,
	Button,
	Container,
	Divider,
	Flex,
	HStack,
	IconButton,
	Input,
	SimpleGrid,
	Text,
	useToast,
	VStack,
} from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";
import { FiFacebook, FiInstagram, FiMail, FiPhone, FiSend, FiTwitter } from "react-icons/fi";
import BrandMark from "./BrandMark";
import { BRAND } from "../brand";

const footerLinks = [
	{
		title: "Shop",
		links: [
			{ label: "The edit", to: "/#edit" },
			{ label: "Collections", to: "/#collections" },
			{ label: "Saved items", to: "/wishlist" },
			{ label: "Your bag", to: "/cart" },
		],
	},
	{
		title: "About",
		links: [
			{ label: "Our story", to: "/#story" },
			{ label: "Studio", to: "/studio" },
			{ label: "Checkout", to: "/checkout" },
			{ label: "Contact", to: "/#newsletter" },
		],
	},
];

const Footer = () => {
	const toast = useToast();

	const handleSubscribe = () => {
		toast({
			title: "You're on the list",
			description: "Welcome to the VELORA inner circle.",
			status: "success",
			duration: 3000,
			isClosable: true,
		});
	};

	return (
		<Box as="footer" bg="velora.ink" color="velora.light" mt={{ base: 16, md: 24 }}>
			<Container maxW="1280px" px={{ base: 4, md: 6, lg: 8 }} py={{ base: 12, md: 16 }}>
				<SimpleGrid columns={{ base: 1, lg: 2 }} spacing={{ base: 12, md: 16 }} pb={14}>
					<VStack align="flex-start" spacing={5} maxW="520px" id="newsletter">
						<HStack spacing={3}>
							<BrandMark size={10} />
							<Text fontFamily="heading" fontSize="2xl" letterSpacing="0.16em">
								{BRAND.name}
							</Text>
						</HStack>
						<Text
							as="h3"
							fontFamily="heading"
							fontSize={{ base: "3xl", md: "4xl" }}
							lineHeight="1.15"
						>
							Join the inner circle.
						</Text>
						<Text color="whiteAlpha.700" fontSize="sm" lineHeight="1.8">
							First access to new arrivals, private edits, and the occasional surprise. No noise, just the good stuff.
						</Text>
						<Flex w="full" maxW="460px" gap={2}>
							<Input
								type="email"
								placeholder="Your email address"
								bg="whiteAlpha.100"
								borderColor="whiteAlpha.200"
								_focusVisible={{ borderColor: "velora.accentLight" }}
								_placeholder={{ color: "whiteAlpha.500" }}
							/>
							<Button
								variant="accent"
								leftIcon={<FiSend />}
								flexShrink={0}
								onClick={handleSubscribe}
							>
								Subscribe
							</Button>
						</Flex>
					</VStack>

					<SimpleGrid columns={{ base: 2, md: 3 }} spacing={8}>
						{footerLinks.map((group) => (
							<VStack align="flex-start" spacing={3} key={group.title}>
								<Text fontSize="xs" letterSpacing="0.18em" textTransform="uppercase" color="velora.accentLight">
									{group.title}
								</Text>
								{group.links.map((link) => (
									<Text
										as={RouterLink}
										to={link.to}
										key={link.label}
										fontSize="sm"
										color="whiteAlpha.700"
										_hover={{ color: "velora.accentLight" }}
									>
										{link.label}
									</Text>
								))}
							</VStack>
						))}
						<VStack align="flex-start" spacing={3}>
							<Text fontSize="xs" letterSpacing="0.18em" textTransform="uppercase" color="velora.accentLight">
								Visit
							</Text>
							<HStack spacing={2} color="whiteAlpha.700" fontSize="sm">
								<FiMail />
								<Text>hello@velora.store</Text>
							</HStack>
							<HStack spacing={2} color="whiteAlpha.700" fontSize="sm">
								<FiPhone />
								<Text>+1 (800) 555-0148</Text>
							</HStack>
							<HStack spacing={2} pt={2}>
								<IconButton
									aria-label="Instagram"
									variant="ghost"
									size="sm"
									color="whiteAlpha.700"
									icon={<FiInstagram />}
									borderRadius="full"
								/>
								<IconButton
									aria-label="Facebook"
									variant="ghost"
									size="sm"
									color="whiteAlpha.700"
									icon={<FiFacebook />}
									borderRadius="full"
								/>
								<IconButton
									aria-label="Twitter"
									variant="ghost"
									size="sm"
									color="whiteAlpha.700"
									icon={<FiTwitter />}
									borderRadius="full"
								/>
							</HStack>
						</VStack>
					</SimpleGrid>
				</SimpleGrid>

				<Divider borderColor="whiteAlpha.200" />
				<Flex
					pt={6}
					direction={{ base: "column", md: "row" }}
					justify="space-between"
					align={{ base: "flex-start", md: "center" }}
					gap={4}
					fontSize="xs"
					color="whiteAlpha.600"
				>
					<Text>© {new Date().getFullYear()} {BRAND.name}. All rights reserved.</Text>
					<HStack spacing={5}>
						<Text>Privacy</Text>
						<Text>Terms</Text>
						<Text>Secure payments</Text>
					</HStack>
				</Flex>
			</Container>
		</Box>
	);
};

export default Footer;
