import os
import requests
from pathlib import Path

def download_file(url, filename):
    """Download a file from URL and save it with the given filename"""
    print(f"  Downloading {filename}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    with open(filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"  ✓ {filename} downloaded")

def parse_version(ver_string):
    """Parse version string into tuple for comparison, handling pre-releases"""
    try:
        # Remove pre-release suffixes like -pre7, -rc1, etc.
        base_version = ver_string.split('-')[0]
        parts = [int(x) for x in base_version.split('.')]
        
        # If it's a pre-release, give it lower priority
        if '-' in ver_string:
            parts.append(-1)  # Pre-releases sort before full releases
        else:
            parts.append(0)   # Full releases
        
        return tuple(parts)
    except ValueError:
        # If parsing fails, return a very low tuple
        return (0, 0, 0, -999)

def get_paper_versions():
    """Get all available Paper versions (excluding pre-releases)"""
    versions_url = "https://api.papermc.io/v2/projects/paper"
    response = requests.get(versions_url)
    data = response.json()
    # Filter out pre-release versions
    return [v for v in data['versions'] if '-' not in v]

def get_geyser_supported_mc_versions():
    """Get Minecraft versions that Geyser supports by checking Modrinth"""
    # Use Modrinth API which lists game version support
    api_url = "https://api.modrinth.com/v2/project/geyser/version"
    response = requests.get(api_url)
    versions = response.json()
    
    # Collect all supported game versions from recent releases
    all_versions = set()
    for version in versions[:5]:  # Check last 5 releases
        all_versions.update(version['game_versions'])
    
    return sorted(all_versions, key=parse_version)

def get_floodgate_supported_mc_versions():
    """Get Minecraft versions that Floodgate supports by checking Modrinth"""
    api_url = "https://api.modrinth.com/v2/project/floodgate/version"
    response = requests.get(api_url)
    versions = response.json()
    
    # Collect all supported game versions from recent releases
    all_versions = set()
    for version in versions[:5]:  # Check last 5 releases
        all_versions.update(version['game_versions'])
    
    return sorted(all_versions, key=parse_version)

def get_viaversion_supported_mc_versions():
    """Get Minecraft versions that ViaVersion supports by checking Modrinth"""
    api_url = "https://api.modrinth.com/v2/project/viaversion/version"
    response = requests.get(api_url)
    versions = response.json()
    
    # Collect all supported game versions from recent releases
    all_versions = set()
    for version in versions[:5]:  # Check last 5 releases
        all_versions.update(version['game_versions'])
    
    return sorted(all_versions, key=parse_version)

def find_best_version():
    """Find the best compatible Minecraft version"""
    print("="*60)
    print("  Checking compatible Minecraft versions...")
    print("="*60)
    
    # Get all available versions
    paper_versions = get_paper_versions()
    geyser_mc_versions = get_geyser_supported_mc_versions()
    floodgate_mc_versions = get_floodgate_supported_mc_versions()
    viaversion_mc_versions = get_viaversion_supported_mc_versions()
    
    # Filter out pre-releases from plugin versions too
    geyser_mc_versions = [v for v in geyser_mc_versions if '-' not in v]
    floodgate_mc_versions = [v for v in floodgate_mc_versions if '-' not in v]
    viaversion_mc_versions = [v for v in viaversion_mc_versions if '-' not in v]
    
    print(f"\n📋 Paper available: {len(paper_versions)} versions")
    print(f"   Latest 3: {', '.join(paper_versions[-3:])}")
    
    print(f"\n🌉 Geyser supports MC versions:")
    for v in sorted(geyser_mc_versions, key=parse_version, reverse=True)[:3]:
        print(f"   • {v}")
    
    print(f"\n💧 Floodgate supports MC versions:")
    for v in sorted(floodgate_mc_versions, key=parse_version, reverse=True)[:3]:
        print(f"   • {v}")
    
    print(f"\n🔮 ViaVersion supports MC versions:")
    for v in sorted(viaversion_mc_versions, key=parse_version, reverse=True)[:3]:
        print(f"   • {v}")
    
    print(f"\n🔍 Finding best match...")
    
    # Find intersection - versions supported by all four
    paper_set = set(paper_versions)
    geyser_set = set(geyser_mc_versions)
    floodgate_set = set(floodgate_mc_versions)
    viaversion_set = set(viaversion_mc_versions)
    
    compatible = paper_set & geyser_set & floodgate_set & viaversion_set
    
    if compatible:
        # Get the highest compatible version
        best = sorted(compatible, key=parse_version)[-1]
        print(f"\n✓ Found perfect match: Minecraft {best}")
        print(f"  All plugins support this version!")
        return best
    
    # If no perfect match, find highest version all four support
    print(f"\n⚠ No exact match found, finding closest compatible version...")
    
    # Find the highest version each supports
    all_versions = sorted(set(paper_versions) | geyser_set | floodgate_set | viaversion_set, key=parse_version)
    
    # Go through versions from highest to lowest
    for version in reversed(all_versions):
        paper_ok = version in paper_set
        geyser_ok = any(parse_version(v) >= parse_version(version) for v in geyser_mc_versions)
        floodgate_ok = any(parse_version(v) >= parse_version(version) for v in floodgate_mc_versions)
        viaversion_ok = any(parse_version(v) >= parse_version(version) for v in viaversion_mc_versions)
        
        if paper_ok and geyser_ok and floodgate_ok and viaversion_ok:
            print(f"\n✓ Found compatible version: Minecraft {version}")
            return version
    
    return None

def download_paper(mc_version):
    """Download Paper for specific version"""
    print(f"\n[1/4] Paper {mc_version}")
    builds_url = f"https://api.papermc.io/v2/projects/paper/versions/{mc_version}"
    response = requests.get(builds_url)
    
    if response.status_code != 200:
        print(f"  ✗ Version {mc_version} not available")
        return False
    
    data = response.json()
    latest_build = data['builds'][-1]
    
    download_url = f"https://api.papermc.io/v2/projects/paper/versions/{mc_version}/builds/{latest_build}/downloads/paper-{mc_version}-{latest_build}.jar"
    download_file(download_url, "paper.jar")
    return True

def download_geyser(mc_version):
    """Download Geyser - get latest build that supports the MC version"""
    print(f"\n[2/4] Geyser")
    
    try:
        # Get the latest Geyser version info
        api_url = "https://download.geysermc.org/v2/projects/geyser/versions/latest/builds/latest"
        response = requests.get(api_url)
        
        if response.status_code == 200:
            build_data = response.json()
            
            # The download name is in the response
            if 'downloads' in build_data and 'spigot' in build_data['downloads']:
                download_name = build_data['downloads']['spigot']['name']
                
                # Construct the proper download URL
                download_url = f"https://download.geysermc.org/v2/projects/geyser/versions/latest/builds/latest/downloads/spigot"
                download_file(download_url, "geyser.jar")
                return True
        
        # Fallback: Try Modrinth
        print("  GeyserMC API failed, trying Modrinth...")
        modrinth_url = "https://api.modrinth.com/v2/project/geyser/version"
        response = requests.get(modrinth_url)
        versions = response.json()
        
        # Find a version that supports our MC version
        for version in versions:
            if mc_version in version['game_versions']:
                # Find the Spigot file
                for file in version['files']:
                    if 'spigot' in file['filename'].lower():
                        download_file(file['url'], "geyser.jar")
                        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    return False

def download_floodgate(mc_version):
    """Download Floodgate - get latest build"""
    print(f"\n[3/4] Floodgate")
    
    try:
        # Try GeyserMC download API first
        api_url = "https://download.geysermc.org/v2/projects/floodgate/versions/latest/builds/latest"
        response = requests.get(api_url)
        
        if response.status_code == 200:
            build_data = response.json()
            
            if 'downloads' in build_data and 'spigot' in build_data['downloads']:
                # Use the correct download path
                download_url = f"https://download.geysermc.org/v2/projects/floodgate/versions/latest/builds/latest/downloads/spigot"
                download_file(download_url, "floodgate.jar")
                return True
        
        # Fallback: Try Modrinth
        print("  Floodgate API failed, trying Modrinth...")
        modrinth_url = "https://api.modrinth.com/v2/project/floodgate/version"
        response = requests.get(modrinth_url)
        versions = response.json()
        
        # Find a version that supports our MC version
        for version in versions:
            if mc_version in version['game_versions']:
                # Find the Spigot file
                for file in version['files']:
                    if 'spigot' in file['filename'].lower():
                        download_file(file['url'], "floodgate.jar")
                        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    return False

def download_viaversion():
    """Download ViaVersion from GitHub"""
    print(f"\n[4/4] ViaVersion")
    
    api_url = "https://api.github.com/repos/ViaVersion/ViaVersion/releases/latest"
    response = requests.get(api_url)
    data = response.json()
    
    for asset in data['assets']:
        if asset['name'].endswith('.jar') and 'sources' not in asset['name']:
            download_file(asset['browser_download_url'], "viaversion.jar")
            return True
    
    return False

def main():
    print("\n" + "="*60)
    print("       Minecraft Server JAR Downloader")
    print("="*60)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    try:
        # Find best compatible version
        mc_version = find_best_version()
        
        if not mc_version:
            print("\n✗ Could not find a compatible version!")
            print("Please check the APIs manually or try again later.")
            return
        
        # Download everything
        print("\n" + "="*60)
        print(f"  Downloading for Minecraft {mc_version}")
        print("="*60)
        
        results = {
            'Paper': download_paper(mc_version),
            'Geyser': download_geyser(mc_version),
            'Floodgate': download_floodgate(mc_version),
            'ViaVersion': download_viaversion()
        }
        
        # Summary
        print("\n" + "="*60)
        print("  Download Summary")
        print("="*60)
        
        success_count = sum(results.values())
        total = len(results)
        
        for name, success in results.items():
            status = "✓" if success else "✗"
            print(f"  {status} {name}")
        
        if success_count == total:
            print(f"\n🎉 All {total} plugins downloaded successfully!")
            print(f"📦 Server version: Minecraft {mc_version}")
            print(f"\n📂 Files saved in: {os.getcwd()}")
            print("   • paper.jar")
            print("   • geyser.jar")
            print("   • floodgate.jar")
            print("   • viaversion.jar")
            print("\n💡 ViaVersion allows players on older Minecraft versions")
            print("   to connect to your server!")
        else:
            print(f"\n⚠ {success_count}/{total} plugins downloaded")
            print("Some downloads failed. Check the output above for details.")
        
        print("="*60)
            
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
