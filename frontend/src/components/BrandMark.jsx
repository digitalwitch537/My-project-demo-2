import { Box, Image } from "@chakra-ui/react";

const BrandMark = ({ size = 9 }) => (
	<Box
		as="span"
		display="inline-flex"
		flexShrink={0}
		borderRadius="lg"
		overflow="hidden"
		boxShadow="0 6px 16px rgba(178, 118, 63, 0.24)"
	>
		<Image src="/velora-mark.svg" alt="VELORA" boxSize={size} />
	</Box>
);

export default BrandMark;
