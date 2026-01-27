# Logic: SVG Chart Output

## User Path
1. The user runs the test script `test_resistance_breakthrough.py`.
2. The script processes stock data and identifies resistance breakthrough points.
3. The script generates a visualization of the results.
4. The system saves the visualization in both PNG (for quick preview) and SVG (for high-quality zoom) formats.
5. The user can access the SVG file in the `output/test_charts/` directory.

## Business Logic
- Multi-format Export: Every time a chart is generated, it should be saved in PNG and SVG.
- File Naming: The SVG file should share the same base name as the PNG but with a `.svg` extension.
- Quality: SVG format is vector-based, ensuring that elements like lines, text, and markers remain sharp at any zoom level.

## Edge Cases
- Directory Missing: The `output/test_charts/` directory should be created if it doesn't exist.
- Font Support: Matplotlib should use appropriate fonts that can be embedded or rendered correctly in SVG.
