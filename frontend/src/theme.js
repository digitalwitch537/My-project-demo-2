import { extendTheme } from "@chakra-ui/react";

const theme = extendTheme({
	config: {
		initialColorMode: "light",
		useSystemColorMode: false,
	},
	fonts: {
		heading: `"Playfair Display", Georgia, serif`,
		body: `"Plus Jakarta Sans", system-ui, sans-serif`,
	},
	colors: {
		velora: {
			ink: "#171512",
			inkSoft: "#2C2823",
			canvas: "#FAF8F5",
			light: "#F7F3ED",
			surface: "#FFFFFF",
			night: "#0E0F12",
			nightSurface: "#17191D",
			muted: "#716B62",
			mutedDark: "#AAA49C",
			line: "#E8E1D7",
			lineDark: "#2C2F35",
			accent: "#B2763F",
			accentHover: "#925B2B",
			accentLight: "#D9A76F",
			accentSoft: "#F5EADB",
		},
	},
	styles: {
		global: {
			body: {
				bg: "velora.canvas",
				color: "velora.ink",
				fontFamily: "body",
				_dark: {
					bg: "velora.night",
					color: "velora.light",
				},
			},
			a: {
				textDecoration: "none",
			},
			"::selection": {
				bg: "velora.accentSoft",
				color: "velora.ink",
			},
		},
	},
	components: {
		Button: {
			baseStyle: {
				fontWeight: "600",
				borderRadius: "full",
				letterSpacing: "0.01em",
				transition: "all 0.25s ease",
			},
			variants: {
				brand: {
					bg: "velora.ink",
					color: "white",
					_hover: { bg: "velora.accent", transform: "translateY(-1px)" },
					_active: { transform: "translateY(0)" },
					_dark: { bg: "velora.light", color: "velora.ink", _hover: { bg: "velora.accentLight" } },
				},
				accent: {
					bg: "velora.accent",
					color: "white",
					_hover: { bg: "velora.accentHover", transform: "translateY(-1px)" },
					_active: { transform: "translateY(0)" },
				},
				outlineInk: {
					border: "1px solid",
					borderColor: "velora.line",
					color: "velora.ink",
					bg: "transparent",
					_hover: { borderColor: "velora.accent", color: "velora.accent", bg: "velora.accentSoft" },
					_dark: {
						borderColor: "velora.lineDark",
						color: "velora.light",
						_hover: { borderColor: "velora.accentLight", color: "velora.accentLight", bg: "velora.nightSurface" },
					},
				},
			},
			defaultProps: {
				variant: "brand",
			},
		},
		Heading: {
			baseStyle: {
				fontFamily: "heading",
				letterSpacing: "-0.025em",
			},
		},
		Input: {
			baseStyle: {
				focusBorderColor: "velora.accent",
				borderRadius: "lg",
			},
		},
		Select: {
			baseStyle: {
				focusBorderColor: "velora.accent",
				borderRadius: "lg",
			},
		},
		Modal: {
			baseStyle: {
				dialog: {
					borderRadius: "2xl",
					overflow: "hidden",
				},
			},
		},
	},
});

export default theme;
