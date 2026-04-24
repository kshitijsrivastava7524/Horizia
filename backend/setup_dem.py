from fetch_dem import fetch_dem
from generate_contour import generate_contour

SITES = ["site1", "site2", "site3", "site4"]

def main():
    for site in SITES:
        print(f"\n[SETUP] {site}")
        dem_path = fetch_dem(site)
        generate_contour(site)

if __name__ == "__main__":
    main()