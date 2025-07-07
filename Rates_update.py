import requests
import json
import csv
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict

def debug_print(message):
    """Print debug messages that will show up in GitHub Actions logs."""
    print(f"DEBUG: {message}", file=sys.stderr)

def parse_date(date_string):
    """Convert API date format to readable format."""
    try:
        return datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S.%fZ').strftime('%B %d, %Y')
    except ValueError:
        return datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%SZ').strftime('%B %d, %Y')

def get_normalized_family(family_type):
    """
    Normalize the benchmark family according to desired grouping:
    - Thematic -> "Sector & Thematic"
    - Sector -> "Sector & Thematic"
    """
    if family_type in ["Thematic", "Sector"]:
        return "Sector & Thematic"
    else:
        return family_type

def get_existing_fact_sheets():
    """Read existing factsheet links from the current CSV."""
    fact_sheets = {}
    csv_path = "Reference_Rates_Coverage.csv"
    debug_print(f"Looking for CSV at: {os.path.abspath(csv_path)}")
    
    if os.path.exists(csv_path):
        debug_print("Found existing CSV file")
        with open(csv_path, "r", newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            factsheet_column = 'Factsheet' if 'Factsheet' in reader.fieldnames else 'Fact Sheet'
            
            for row_num, row in enumerate(reader, start=1):
                if factsheet_column in row:
                    value = row.get(factsheet_column, "").strip()
                    # Remove any trailing commas from factsheet values
                    if value.endswith(','):
                        value = value[:-1]
                    
                    if value:
                        ticker = row.get('Ticker', 'Unknown')
                        debug_print(f"Found factsheet for ticker {ticker} at row {row_num}")
                        
                        # Fix double href tags if present
                        if '<a href="<a href="' in value:
                            value = value.replace('<a href="<a href="', '<a href="')
                        
                        fact_sheets[ticker] = value
    
    debug_print(f"Total factsheets found: {len(fact_sheets)}")
    return fact_sheets

def get_base_ticker(ticker):
    """Extract base ticker from location-based variants."""
    # Remove location suffixes
    for suffix in ['NYC', 'LDN', 'SGP']:
        if ticker.endswith(suffix):
            return ticker[:-len(suffix)]
    return ticker

def get_location_from_ticker(ticker):
    """Extract location from ticker if present."""
    for suffix in ['NYC', 'LDN', 'SGP']:
        if ticker.endswith(suffix):
            return suffix
    return None

def get_fixed_entries():
    """Return a list of fixed index entries that should always be included."""
    factsheet_blue_chip = '<a href="https://marketing.kaiko.com/hubfs/Factsheets%20and%20Methodologies/New%20Benchmark%20Factsheets/Kaiko%20Benchmarks%20-%20Blue-Chip%20family%20factsheet.pdf" target="_blank">View Factsheet</a>'
    factsheet_sector_thematic = '<a href="https://marketing.kaiko.com/hubfs/Factsheets%20and%20Methodologies/New%20Benchmark%20Factsheets/Kaiko%20Benchmarks%20-%20Sector%20&%20Thematic%20family%20factsheet.pdf" target="_blank">View Factsheet</a>'
    factsheet_market = '<a href="https://marketing.kaiko.com/hubfs/Factsheets%20and%20Methodologies/New%20Benchmark%20Factsheets/Kaiko%20Benchmarks%20-%20Market%20family%20factsheet.pdf" target="_blank">View Factsheet</a>'
    
    # Return all entries with the new structure (Brand, Family, Name, Ticker, Disseminations, Launch Date, Inception Date, Factsheet)
    return [
        # Blue-Chip Indices
        ('Kaiko', 'Blue-Chip', 'Kaiko Eagle Index', 'EGLX', 'NYC Fixing', 'February 11, 2025', 'February 11, 2025', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko Eagle Index', 'EGLXRT', 'Real-time (5 sec)', 'February 11, 2025', 'February 11, 2025', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko 5 Index', 'KT5', 'Real-time (5 sec)', 'October 17, 2023', 'March 19, 2018', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko 5 Index NYC', 'KT5NYC', 'NYC Fixing', 'October 17, 2023', 'March 19, 2018', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko 5 Index LDN', 'KT5LDN', 'LDN Fixing', 'October 17, 2023', 'March 19, 2018', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko 5 Index SGP', 'KT5SGP', 'SGP Fixing', 'October 17, 2023', 'March 19, 2018', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko 10 Index', 'KT10', 'Real-time (5 sec)', 'October 17, 2023', 'March 18, 2019', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko 10 Index NYC', 'KT10NYC', 'NYC Fixing', 'October 17, 2023', 'March 18, 2019', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko 10 Index LDN', 'KT10LDN', 'LDN Fixing', 'October 17, 2023', 'March 18, 2019', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko 10 Index SGP', 'KT10SGP', 'SGP Fixing', 'October 17, 2023', 'March 18, 2019', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko 15 Index', 'KT15', 'Real-time (5 sec)', 'October 17, 2023', 'December 23, 2019', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko 15 Index NYC', 'KT15NYC', 'NYC Fixing', 'October 17, 2023', 'December 23, 2019', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko 15 Index LDN', 'KT15LDN', 'LDN Fixing', 'October 17, 2023', 'December 23, 2019', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Kaiko 15 Index SGP', 'KT15SGP', 'SGP Fixing', 'October 17, 2023', 'December 23, 2019', factsheet_blue_chip),
        ('Kaiko', 'Blue-Chip', 'Vinter 21Shares Crypto Basket Equal Weight Index ', 'HODLV', 'LDN Fixing', 'September 29, 2021', 'January 01, 2021', '<a href="https://marketing.kaiko.com/hubfs/Factsheets%20and%20Methodologies/multi-asset_hodlv_end=2025-03-12&start=2020-12-31.pdf" target="_blank">View Factsheet</a>'),
        ('Kaiko', 'Blue-Chip', 'Vinter 21Shares Crypto Basket 10 Index', 'HODLX', 'LDN Fixing', 'September 29, 2021', 'January 01, 2021', '<a target="_blank">Coming Soon</a>'),
        ('Kaiko', 'Blue-Chip', 'Vinter Valour Digital Asset Basket 10 Index', 'VDAB10', 'LDN Fixing', 'July 21, 2022', 'January 01, 2021', '<a href="https://marketing.kaiko.com/hubfs/Factsheets%20and%20Methodologies/VDAB10%20-%20Fact%20Sheet%20-%20multi-asset_vdab10_end=2025-03-12&start=2020-12-31.pdf" target="_blank">View Factsheet</a>'),
        ('Kaiko', 'Blue-Chip', 'Vinter Pando Crypto Basket 6 Index ', 'PANDO6', '17:00 CET Fixing', 'July 21, 2022', 'January 01, 2021', '<a href="https://marketing.kaiko.com/hubfs/Factsheets%20and%20Methodologies/PANDO6%20-%20Fact%20Sheet%20-%20multi-asset_pando6_end=2025-03-12&start=2020-12-31.pdf" target="_blank">View Factsheet</a>'),
        ('Kaiko', 'Blue-Chip', 'Virtune Vinter Crypto Top 10 Index', 'VVT10', '17:00 CET Fixing', 'March 31, 2023', 'January 01, 2021', '<a href="https://marketing.kaiko.com/hubfs/Factsheets%20and%20Methodologies/VVT10%20-%20Fact%20Sheet%20-%20multi-asset_vvt10_end=2025-03-12&start=2020-12-31.pdf" target="_blank">View Factsheet</a>'),
        
        # Sector & Thematic Indices
        ('Kaiko', 'Sector & Thematic', 'Kaiko Tokenization Index', 'KSTKNZ', 'Real-time (5 sec)', 'January 23, 2025', 'January 3, 2022', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko Tokenization Index NYC', 'KSTKNZNYC', 'NYC Fixing', 'January 23, 2025', 'January 3, 2022', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko Tokenization Index LDN', 'KSTKNZLDN', 'LDN Fixing', 'January 23, 2025', 'January 3, 2022', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko Tokenization Index SGP', 'KSTKNZSGP', 'SGP Fixing', 'January 23, 2025', 'January 3, 2022', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko AI Index', 'KSAI', 'Real-time (5 sec)', 'January 23, 2025', 'October 3, 2022', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko AI Index NYC', 'KSAINYC', 'NYC Fixing', 'January 23, 2025', 'October 3, 2022', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko AI Index LDN', 'KSAILDN', 'LDN Fixing', 'January 23, 2025', 'October 3, 2022', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko AI Index SGP', 'KSAISGP', 'SGP Fixing', 'January 23, 2025', 'October 3, 2022', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko Meme Index', 'KSMEME', 'Real-time (5 sec)', 'January 22, 2025', 'April 3, 2023', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko Meme Index NYC', 'KSMEMENYC', 'NYC Fixing', 'January 22, 2025', 'April 3, 2023', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko Meme Index LDN', 'KSMEMELDN', 'LDN Fixing', 'January 22, 2025', 'April 3, 2023', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko Meme Index SGP', 'KSMEMESGP', 'SGP Fixing', 'January 22, 2025', 'April 3, 2023', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko DeFi Index', 'KSDEFI', 'Real-time (5 sec)', 'January 17, 2025', 'April 3, 2023', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko DeFi Index NYC', 'KSDEFINYC', 'NYC Fixing', 'January 17, 2025', 'April 3, 2023', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko DeFi Index LDN', 'KSDEFILDN', 'LDN Fixing', 'January 17, 2025', 'April 3, 2023', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko DeFi Index SGP', 'KSDEFISGP', 'SGP Fixing', 'January 17, 2025', 'April 3, 2023', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko L2 Index', 'KSL2', 'Real-time (5 sec)', 'July 2, 2024', 'April 3, 2023', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko L2 Index NYC', 'KSL2NYC', 'NYC Fixing', 'July 2, 2024', 'April 3, 2023', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko L2 Index LDN', 'KSL2LDN', 'LDN Fixing', 'July 2, 2024', 'April 3, 2023', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Kaiko L2 Index SGP', 'KSL2SGP', 'SGP Fixing', 'July 2, 2024', 'April 3, 2023', factsheet_sector_thematic),
        ('Kaiko', 'Sector & Thematic', 'Vinter Cardano Yield Index ', 'CASL', 'LDN Fixing', 'November 10, 2022', 'March 06, 2024', '<a href="https://marketing.kaiko.com/hubfs/Factsheets%20and%20Methodologies/CASL%20-%20Fact%20Sheet%20-%20multi-asset_casl_end=2025-03-12&start=2020-12-31.pdf" target="_blank">View Factsheet</a>'),
        ('Kaiko', 'Sector & Thematic', 'Sygnum Platform Winners Index ', 'MOON', '17:00 CET Fixing', 'July 21, 2022', 'November 01, 2019', '<a href="https://marketing.kaiko.com/hubfs/Factsheets%20and%20Methodologies/MOON%20-%20Fact%20Sheet%20-%20multi-asset_moon_end=2025-03-12&start=2020-12-31.pdf" target="_blank">View Factsheet</a>'),
        ('Kaiko', 'Sector & Thematic', 'Vinter CF Crypto Web3 Index', 'VCFWB3', 'LDN Fixing', 'May 15, 2023', 'January 01, 2021', '<a href="https://marketing.kaiko.com/hubfs/Factsheets%20and%20Methodologies/VCFWB3%20-%20Fact%20Sheet%20-multi-asset_vcfwb3_end=2025-03-12&start=2020-12-31.pdf" target="_blank">View Factsheet</a>'),
        
        # Market Indices
        ('Kaiko', 'Market', 'Kaiko Standard Index', 'KMSTA', 'Real-time (5 sec)', 'January 23, 2025', 'April 1, 2014', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Standard Index NYC', 'KMSTANYC', 'NYC Fixing', 'January 23, 2025', 'April 1, 2014', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Standard Index LDN', 'KMSTALDN', 'LDN Fixing', 'January 23, 2025', 'April 1, 2014', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Standard Index SGP', 'KMSTASGP', 'SGP Fixing', 'January 23, 2025', 'April 1, 2014', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Small Cap Index', 'KMSMA', 'Real-time (5 sec)', 'January 23, 2025', 'January 2, 2015', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Small Cap Index NYC', 'KMSMANYC', 'NYC Fixing', 'January 23, 2025', 'January 2, 2015', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Small Cap Index LDN', 'KMSMALDN', 'LDN Fixing', 'January 23, 2025', 'January 2, 2015', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Small Cap Index SGP', 'KMSMASGP', 'SGP Fixing', 'January 23, 2025', 'January 2, 2015', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Mid Cap Index', 'KMMID', 'Real-time (5 sec)', 'January 23, 2025', 'April 2, 2018', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Mid Cap Index NYC', 'KMMIDNYC', 'NYC Fixing', 'January 23, 2025', 'April 2, 2018', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Mid Cap Index LDN', 'KMMIDLDN', 'LDN Fixing', 'January 23, 2025', 'April 2, 2018', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Mid Cap Index SGP', 'KMMIDSGP', 'SGP Fixing', 'January 23, 2025', 'April 2, 2018', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Large Cap Index', 'KMLAR', 'Real-time (5 sec)', 'January 23, 2025', 'April 1, 2014', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Large Cap Index NYC', 'KMLARNYC', 'NYC Fixing', 'January 23, 2025', 'April 1, 2014', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Large Cap Index LDN', 'KMLARLDN', 'LDN Fixing', 'January 23, 2025', 'April 1, 2014', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Large Cap Index SGP', 'KMLARSGP', 'SGP Fixing', 'January 23, 2025', 'April 1, 2014', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Investable Index', 'KMINV', 'Real-time (5 sec)', 'January 23, 2025', 'April 1, 2014', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Investable Index NYC', 'KMINVNYC', 'NYC Fixing', 'January 23, 2025', 'April 1, 2014', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Investable Index LDN', 'KMINVLDN', 'LDN Fixing', 'January 23, 2025', 'April 1, 2014', factsheet_market),
        ('Kaiko', 'Market', 'Kaiko Investable Index SGP', 'KMINVSGP', 'SGP Fixing', 'January 23, 2025', 'April 1, 2014', factsheet_market),
        ('Kaiko', 'Market', 'Vinter 21Shares Crypto Mid-Cap Index ', 'ALTS', 'LDN Fixing', 'December 14, 2021', 'January 01, 2021', '<a href="https://marketing.kaiko.com/hubfs/Factsheets%20and%20Methodologies/ALTS%20-%20Fact%20Sheet%20-%20multi-asset_alts_end=2025-03-12&start=2020-12-31.pdf" target="_blank">View Factsheet</a>'),
        ('Kaiko', 'Market', 'Vinter 21Shares Crypto Staking Index ', 'STAKE', 'LDN Fixing', 'January 18, 2023', 'January 01, 2021', '<a href="https://marketing.kaiko.com/hubfs/Factsheets%20and%20Methodologies/multi-asset_stake_end=2025-03-12&start=2020-12-31.pdf" target="_blank">View Factsheet</a>'),
        ('Kaiko', 'Market', 'Vinter BOLD Index', 'VBNGD', 'LDN Fixing', 'November 10, 2023', 'January 01, 2020', '<a href="https://marketing.kaiko.com/hubfs/Factsheets%20and%20Methodologies/VBNGD%20-%20Fact%20Sheet%20-%20multi-asset_vbngd_end=2025-03-12&start=2020-12-31.pdf" target="_blank">View Factsheet</a>'),
        ('Kaiko', 'Market', 'Vinter CF Crypto Momentum Index', 'VCFMOM', 'LDN Fixing', 'May 15, 2023', 'January 01, 2021', '<a href="https://marketing.kaiko.com/hubfs/Factsheets%20and%20Methodologies/VCFMOM%20-%20Fact%20Sheet%20-multi-asset_vcfmom_end=2025-03-12&start=2020-12-31.pdf" target="_blank">View Factsheet</a>'),
        ('Kaiko', 'Market', 'Vinter Diffuse Digital 30 Index', 'DDV', 'LDN Fixing', 'July 02, 2022', 'January 01, 2021', '<a href="https://marketing.kaiko.com/hubfs/Factsheets%20and%20Methodologies/DDV%20-%20Fact%20Sheet%20-%20multi-asset_ddv_end=2025-03-12&start=2020-12-31.pdf" target="_blank">View Factsheet</a>'),
        ('Kaiko', 'Market', 'Vinter Hashdex Risk Parity Momentum Crypto Index', 'VHASHMOM', '17:00 CET Fixing', 'September 05, 2022', 'January 01, 2021', '<a href="https://marketing.kaiko.com/hubfs/VHASHMOM%20Kaiko%20Factsheet.pdf" target="_blank">View Factsheet</a>'),
        ('Kaiko', 'Market', 'Vinter Bytetree BOLD1 Inverse Volatility Index', 'BOLD1', 'LDN Fixing', 'November 10, 2023', 'January 01, 2020', '<a target="_blank">Coming Soon</a>')
    ]

def merge_location_variants(items):
    """Merge location-based variants into single rows with combined disseminations."""
    debug_print("Starting merge of location variants")
    
    # Group items by base ticker
    ticker_groups = defaultdict(list)
    for item in items:
        ticker = item[3]  # Ticker is at index 3
        base_ticker = get_base_ticker(ticker)
        ticker_groups[base_ticker].append(item)
    
    merged_items = []
    
    for base_ticker, variants in ticker_groups.items():
        debug_print(f"Processing base ticker: {base_ticker} with {len(variants)} variants")
        
        # Find the base variant (without location suffix)
        base_variant = None
        location_variants = []
        
        for variant in variants:
            ticker = variant[3]
            if ticker == base_ticker:
                base_variant = variant
            else:
                location_variants.append(variant)
        
        if base_variant is None:
            # If no base variant found, use the first one as base
            base_variant = variants[0]
            location_variants = variants[1:]
        
        # Build disseminations string
        disseminations = [base_variant[4]]  # Start with base dissemination
        
        # Add location disseminations in order: NYC, LDN, SGP
        locations_found = []
        for location in ['NYC', 'LDN', 'SGP']:
            for variant in location_variants:
                ticker = variant[3]
                if ticker.endswith(location):
                    locations_found.append(location)
                    break
        
        if locations_found:
            disseminations.extend(locations_found)
        
        combined_disseminations = ', '.join(disseminations)
        
        # Create merged entry using base variant's data
        merged_entry = (
            base_variant[0],  # Brand
            base_variant[1],  # Benchmark Family
            base_variant[2],  # Name
            base_ticker,      # Use base ticker
            combined_disseminations,  # Combined disseminations
            base_variant[5],  # Launch Date
            base_variant[6],  # Inception Date
            base_variant[7]   # Factsheet
        )
        
        merged_items.append(merged_entry)
        debug_print(f"Merged {base_ticker}: {combined_disseminations}")
    
    debug_print(f"Merged {len(items)} items into {len(merged_items)} entries")
    return merged_items

def write_filtered_csv(items, headers):
    """Write a filtered CSV with only the entries that have factsheets."""
    filtered_csv_path = "Reference_Rates_With_Factsheets.csv"
    
    # Filter items that have factsheets
    filtered_items = []
    for item in items:
        if item[-1] and item[-1] != '-' and item[-1] != '':
            filtered_items.append(item)
    
    debug_print(f"Writing filtered CSV with {len(filtered_items)} entries")
    
    with open(filtered_csv_path, "w", newline='') as csv_file:
        writer = csv.writer(csv_file, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(headers)
        writer.writerows(filtered_items)
    
    debug_print(f"Filtered CSV saved to {filtered_csv_path}")

def pull_and_save_data_to_csv():
    """Process static indices and save them to CSV."""
    debug_print("Starting data pull and save process for static indices only")
    existing_fact_sheets = get_existing_fact_sheets()
    fixed_items = get_fixed_entries()
    
    # New headers without Base, Quote, Exchanges, Calculation Window
    headers = [
        'Brand', 'Benchmark Family', 'Name', 'Ticker', 'Disseminations', 'Launch Date', 'Inception Date', 'Factsheet'
    ]
    
    # Process fixed items with factsheets
    fixed_items_with_fact_sheets = []
    for entry in fixed_items:
        ticker = entry[3]
        # Use either the factsheet from fixed data or from existing CSV
        factsheet = entry[7]  # Factsheet is now at index 7
        if ticker in existing_fact_sheets and existing_fact_sheets[ticker]:
            factsheet = existing_fact_sheets[ticker]
            if factsheet.endswith(','):
                factsheet = factsheet[:-1]
        
        fixed_items_with_fact_sheets.append(entry[:7] + (factsheet,))
    
    debug_print(f"Processing {len(fixed_items_with_fact_sheets)} fixed items")
    
    # Merge location variants
    merged_items = merge_location_variants(fixed_items_with_fact_sheets)
    
    # Sort by ticker
    all_items = sorted(merged_items, key=lambda row: row[3])
    
    debug_print(f"Final item count: {len(all_items)}")
    
    # Save to CSV
    main_csv_path = "Reference_Rates_Coverage.csv"
    debug_print(f"Saving main CSV to {os.path.abspath(main_csv_path)}")
    with open(main_csv_path, "w", newline='') as csv_file:
        writer = csv.writer(csv_file, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(headers)
        writer.writerows(all_items)
    
    # Write the filtered CSV with only entries that have factsheets
    write_filtered_csv(all_items, headers)
    debug_print("Process complete")

# Main execution
if __name__ == "__main__":
    debug_print("Starting script execution...")
    debug_print("Repository: https://github.com/rdavill/kaiko_indices_coverage_multi")
    debug_print("Processing static indices only (no API calls for single assets)")
    
    pull_and_save_data_to_csv()
