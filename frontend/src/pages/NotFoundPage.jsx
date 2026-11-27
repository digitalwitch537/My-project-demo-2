import {
	Button,
	Container,
	Heading,
	Text,
	VStack,
} from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";
import { FiArrowRight } from "react-icons/fi";

const NotFoundPage = () => (
	<Container maxW="container.md" px={6} py={{ base: 24, md: 36 }}>
		<VStack spacing={6} textAlign="center">
			<Text fontFamily="heading" fontSize="8xl" color="velora.accent" lineHeight="1">404</Text>
			<Heading fontSize={{ base: "3xl", md: "5xl" }}>This page took a different turn.</Heading>
			<Text color="velora.muted" fontSize="sm">
				The piece you&apos;re looking for isn&apos;t in this edit.
			</Text>
			<Button as={RouterLink} to="/" variant="accent" rightIcon={<FiArrowRight />}>
				Back to the store
			</Button>
		</VStack>
	</Container>
);

export default NotFoundPage;
