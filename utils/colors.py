"""
Color pallets!
"""
from discord import Colour

__all__ = (
    'DiscordColorPallets',
    'PantoneColors'
)


class DiscordColorPallets:
    """
    Discord Color Pallet
    """
    Green = Colour.green()
    Red = Colour.red()
    Blurple = Colour.blurple()


class PantoneColors:
    """
    Pantone Colors
    """
    DarkBlueC = Colour.from_rgb(0, 36, 156)
    Yellow012C = Colour.from_rgb(255, 215, 0)
    BrightRedC = Colour.from_rgb(249, 56, 34)
    StarSapphire = Colour.from_rgb(56, 97, 146)