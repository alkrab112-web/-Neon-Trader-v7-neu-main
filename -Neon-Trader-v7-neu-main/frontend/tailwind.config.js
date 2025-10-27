/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: ["class"],
    content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
  	extend: {
  		// Neon Trader V7 Custom Properties
  		fontFamily: {
  			'tajawal': ['Tajawal', 'Arial', 'sans-serif'],
  			'sans': ['Tajawal', 'system-ui', 'sans-serif'],
  		},
  		borderRadius: {
  			lg: 'var(--radius)',
  			md: 'calc(var(--radius) - 2px)',
  			sm: 'calc(var(--radius) - 4px)',
  			'2xl': '1rem',
  			'3xl': '1.5rem',
  		},
  		colors: {
  			// Original shadcn colors
  			background: 'hsl(var(--background))',
  			foreground: 'hsl(var(--foreground))',
  			card: {
  				DEFAULT: 'hsl(var(--card))',
  				foreground: 'hsl(var(--card-foreground))'
  			},
  			popover: {
  				DEFAULT: 'hsl(var(--popover))',
  				foreground: 'hsl(var(--popover-foreground))'
  			},
  			primary: {
  				DEFAULT: 'hsl(var(--primary))',
  				foreground: 'hsl(var(--primary-foreground))'
  			},
  			secondary: {
  				DEFAULT: 'hsl(var(--secondary))',
  				foreground: 'hsl(var(--secondary-foreground))'
  			},
  			muted: {
  				DEFAULT: 'hsl(var(--muted))',
  				foreground: 'hsl(var(--muted-foreground))'
  			},
  			accent: {
  				DEFAULT: 'hsl(var(--accent))',
  				foreground: 'hsl(var(--accent-foreground))'
  			},
  			destructive: {
  				DEFAULT: 'hsl(var(--destructive))',
  				foreground: 'hsl(var(--destructive-foreground))'
  			},
  			border: 'hsl(var(--border))',
  			input: 'hsl(var(--input))',
  			ring: 'hsl(var(--ring))',
  			chart: {
  				'1': 'hsl(var(--chart-1))',
  				'2': 'hsl(var(--chart-2))',
  				'3': 'hsl(var(--chart-3))',
  				'4': 'hsl(var(--chart-4))',
  				'5': 'hsl(var(--chart-5))'
  			},
  			// Neon Theme Colors - As per document
  			neon: {
  				cyan: '#00fff2',
  				magenta: '#ff0077',
  				background: '#0b0e17',
  				text: '#e0e0e0',
  			},
  			glass: {
  				bg: 'rgba(255, 255, 255, 0.05)',
  				border: 'rgba(0, 255, 242, 0.2)',
  			}
  		},
  		backdropBlur: {
  			'xs': '2px',
  			'xl': '20px',
  			'2xl': '24px',
  			'3xl': '32px',
  		},
  		boxShadow: {
  			'neon-cyan': '0 0 20px #00fff2, 0 0 40px #00fff2, 0 0 80px #00fff2',
  			'neon-magenta': '0 0 20px #ff0077, 0 0 40px #ff0077, 0 0 80px #ff0077',
  			'glass': '0 8px 32px rgba(0, 255, 242, 0.1)',
  			'glass-lg': '0 20px 60px rgba(0, 255, 242, 0.2)',
  		},
  		keyframes: {
  			// Neon animations
  			'neon-pulse': {
  				'0%, 100%': { 
  					boxShadow: '0 0 5px currentColor, 0 0 10px currentColor, 0 0 15px currentColor' 
  				},
  				'50%': { 
  					boxShadow: '0 0 10px currentColor, 0 0 20px currentColor, 0 0 30px currentColor' 
  				}
  			},
  			'gradient-xy': {
  				'0%, 100%': {
  					'background-size': '400% 400%',
  					'background-position': 'left center'
  				},
  				'50%': {
  					'background-size': '200% 200%',
  					'background-position': 'right center'
  				}
  			},
  			'float': {
  				'0%, 100%': { transform: 'translateY(0px)' },
  				'50%': { transform: 'translateY(-20px)' }
  			},
  			'glow': {
  				'0%, 100%': { opacity: '1' },
  				'50%': { opacity: '0.5' }
  			},
  			'accordion-down': {
  				from: {
  					height: '0'
  				},
  				to: {
  					height: 'var(--radix-accordion-content-height)'
  				}
  			},
  			'accordion-up': {
  				from: {
  					height: 'var(--radix-accordion-content-height)'
  				},
  				to: {
  					height: '0'
  				}
  			}
  		},
  		animation: {
  			'accordion-down': 'accordion-down 0.2s ease-out',
  			'accordion-up': 'accordion-up 0.2s ease-out',
  			// Neon animations
  			'neon-pulse': 'neon-pulse 2s ease-in-out infinite',
  			'gradient-xy': 'gradient-xy 15s ease infinite',
  			'float': 'float 6s ease-in-out infinite',
  			'glow': 'glow 2s ease-in-out infinite alternate'
  		}
  	}
  },
  plugins: [require("tailwindcss-animate")],
};