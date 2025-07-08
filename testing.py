# testing.py

from generator import QuoteGenerator

g = QuoteGenerator()

g.generate(
    date="2025.07.02",
    author="Einstein",
    quote="Imagination is more important than knowledge.",
    output_format="jpeg"
)
