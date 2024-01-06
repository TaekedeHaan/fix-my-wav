# type: ignore
import discogs_client

def print_release(release: discogs_client.Release):
    print(f"Release: {release.title}")
    print(f" - id: {release.id}")
    print(f" - artists: {", ".join([artist.name for artist in release.artists])}")
    print(f" - year: {release.year}")
    print(f" - data quality: {release.data_quality}")
    print(f" - styles: {(', '.join(release.styles) if release.styles else "None")}")
    print(f" - genres: {(', '.join(release.genres) if release.genres else "None")}")
    print(f" - url {release.url}")


def print_master(master: discogs_client.Master):
    print(f"Master release {master.title}")
    print(f" - id: {master.id}")
    print(f" - year: {master.year}")
    print(f" - data quality: {master.data_quality}")
    print(f" - styles: {(', '.join(master.styles) if master.styles else "None")}")
    print(f" - genres: {(', '.join(master.genres) if master.genres else "None")}")
    print(f" - url {master.url}")

def print_artist(artist: discogs_client.Artist):
    print(f"Name: {artist.name}")
