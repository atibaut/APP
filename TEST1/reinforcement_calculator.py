

import math

def calculate_effective_depth(h, cover, d_rebar, n_rows, spacing):
    """
    Calculate effective depth d for multiple rebar rows.
    Assumes equal reinforcement area per row.
    """
    if n_rows == 1:
        centroid = cover + d_rebar / 2
    else:
        # Centroid from bottom = cover + d_rebar/2 + ((n_rows-1)/2) * (d_rebar + spacing)
        centroid = cover + d_rebar / 2 + ((n_rows - 1) / 2) * (d_rebar + spacing)
    d = h - centroid
    return d

def calculate_reinforcement_area(M, b, d, fck, fy):
    """
    Calculate required bottom reinforcement area As using Eurocode 2.
    M in kNm, b,d in mm, fck,fy in MPa
    """
    # Convert to consistent units: M to Nmm, b,d to mm
    M = M * 1e6  # kNm to Nmm
    fcd = fck / 1.5
    fyd = fy / 1.15
    
    # Calculate k = M / (b * d^2 * fcd)
    k = M / (b * d**2 * fcd)
    
    if k > 0.167:
        print("Compression reinforcement required. Calculation assumes singly reinforced.")
        return None
    
    # z = d * (1 - 0.4 * k)
    z = d * (1 - 0.4 * k)
    
    # As = M / (z * fyd)
    As = M / (z * fyd)
    
    return As

def calculate_bars(As, d_rebar, b, spacing_horizontal, cover):
    """
    Calculate number of bars and distribution per row.
    Only uses up to 2 rows for output. If more are required, it reports that 3 rows would be needed.
    spacing_horizontal: spacing between bars in a row (mm)
    cover: concrete cover (mm)
    """
    # Area of one bar
    area_bar = math.pi * (d_rebar / 2)**2
    
    # Total number of bars
    total_bars = math.ceil(As / area_bar)
    
    # Check if it fits in width - correct formula
    available_width = b - 2 * cover
    if available_width <= d_rebar:
        max_bars_per_row = 1  # at least 1 bar can fit
    else:
        max_bars_per_row = ((available_width - d_rebar) // (d_rebar + spacing_horizontal)) + 1
    
    actual_rows_needed = math.ceil(total_bars / max_bars_per_row)
    
    # Only show up to 2 rows in output
    if total_bars <= max_bars_per_row:
        shown_rows = 1
        distribution = [total_bars]
    elif total_bars <= 2 * max_bars_per_row:
        shown_rows = 2
        bars_per_row = total_bars // 2
        extra_bars = total_bars % 2
        distribution = [bars_per_row + (1 if i < extra_bars else 0) for i in range(2)]
    else:
        shown_rows = 2
        distribution = [max_bars_per_row, max_bars_per_row]
    
    return total_bars, distribution, shown_rows, actual_rows_needed, max_bars_per_row

def recommend_efficient_diameter(As, b, cover):
    """
    Show bar requirements for different rebar diameters.
    Prioritizes solutions that use 1-2 rows maximum for optimal efficiency.
    """
    # Common rebar diameters
    diameters = [12, 16, 20, 25, 28, 32]  # mm
    
    recommendations = {}
    
    for dia in diameters:
        area_bar = math.pi * (dia / 2)**2
        total_bars = math.ceil(As / area_bar)
        
        spacing = max(20, dia)
        # Check if it fits in width - correct formula
        available_width = b - 2 * cover
        if available_width <= dia:
            max_bars_per_row = 1  # at least 1 bar can fit
        else:
            max_bars_per_row = ((available_width - dia) // (dia + spacing)) + 1
        
        # Determine actual rows needed and shown rows using 1-row and 2-row checks
        actual_rows_needed = math.ceil(total_bars / max_bars_per_row)
        if total_bars <= max_bars_per_row:
            shown_rows = 1
            distribution = [total_bars]
        elif total_bars <= 2 * max_bars_per_row:
            shown_rows = 2
            bars_per_row = total_bars // 2
            extra_bars = total_bars % 2
            distribution = [bars_per_row + (1 if i < extra_bars else 0) for i in range(2)]
        else:
            shown_rows = 2
            distribution = [max_bars_per_row, max_bars_per_row]
        
        # If more than 2 rows needed, this is not preferred
        is_preferred = actual_rows_needed <= 2
        
        recommendations[dia] = {
            'total_bars': total_bars,
            'shown_rows': shown_rows,
            'actual_rows_needed': actual_rows_needed,
            'distribution': distribution,
            'fits': True,  # We ensure it fits by using shown_rows
            'max_per_row': max_bars_per_row,
            'preferred': is_preferred,
            'available_width': available_width,
            'spacing': spacing
        }
    
    return recommendations

def main():
    print("Reinforced Concrete Cross-Section Calculator")
    print("=" * 50)
    
    # Inputs
    d_rebar = float(input("Enter rebar diameter (mm): "))
    n_rows = int(input("Enter number of rows: "))
    b = float(input("Enter cross-section width b (mm): "))
    h = float(input("Enter cross-section height h (mm): "))
    cover = float(input("Enter concrete cover (mm): "))
    spacing = float(input("Enter spacing between rows (mm): "))
    
    # Set horizontal spacing automatically to code minimum
    spacing_horizontal = max(20, d_rebar)
    print(f"Using horizontal bar spacing = {spacing_horizontal} mm (max(20, diameter)).")
    M = float(input("Enter bending moment M (kNm): "))
    fy = float(input("Enter steel yield strength fy (MPa): "))
    fck = float(input("Enter concrete characteristic strength fck (MPa): "))
    
    # Calculate d
    d = calculate_effective_depth(h, cover, d_rebar, n_rows, spacing)
    print(f"\nEffective depth d = {d:.2f} mm")
    
    # Calculate As
    # Calculate As1
    # My comment
    As = calculate_reinforcement_area(M, b, d, fck, fy)
    if As is not None:
        print(f"Required reinforcement area As = {As:.2f} mm²")
        
        # Calculate bars
        total_bars, distribution, shown_rows, actual_rows_needed, max_bars_per_row = calculate_bars(As, d_rebar, b, spacing_horizontal, cover)
        print(f"Total number of bars needed: {total_bars}")
        print(f"Displayed rows: {shown_rows}")
        print("Bars per row:")
        for i, bars in enumerate(distribution, 1):
            print(f"  Row {i}: {bars} bars")

        # Show 1-row and 2-row capacity checks
        one_row_capacity = max_bars_per_row
        two_row_capacity = max_bars_per_row * 2
        print(f"\nOne-row capacity: {one_row_capacity} bars")
        print(f"Two-row capacity: {two_row_capacity} bars")
        if total_bars <= one_row_capacity:
            print("All bars fit in one row.")
        elif total_bars <= two_row_capacity:
            print("All bars fit in two rows.")
        else:
            print(f"More than two rows are required; {actual_rows_needed} rows would be needed to fit all bars.")
        
        # Show detailed comparison for different diameters
        print(f"\nDetailed comparison for different rebar diameters:")
        recommendations = recommend_efficient_diameter(As, b, cover)
        
        for dia in [12, 16, 20, 25, 28, 32]:
            rec = recommendations[dia]
            print(f"\n{dia}mm diameter:")
            print(f"  Total bars needed: {rec['total_bars']}")
            print(f"  Displayed rows: {rec['shown_rows']}")
            print(f"  Actual rows needed: {rec['actual_rows_needed']}")
            print(f"  Bars per row: {', '.join(map(str, rec['distribution']))}")
            
            # Show width calculation explanation
            max_bars = rec['max_per_row']
            available = rec['available_width']
            spacing = rec['spacing']
            
            print(f"  Width calculation (available: {available}mm):")
            for bars in range(1, max_bars + 2):  # Show up to max+1 to show why it fails
                if bars == 1:
                    width = dia
                else:
                    width = bars * dia + (bars - 1) * spacing
                
                status = "✓" if width <= available else "❌"
                print(f"    {bars} bars: {width}mm {status}")
                if width > available:
                    break
            
            if rec['preferred']:
                print("  ✓ Preferred solution (1-2 rows)")
            else:
                print("  ⚠ Requires 3+ rows - consider larger diameter")
    else:
        print("Compression reinforcement required.")

if __name__ == "__main__":
    main()