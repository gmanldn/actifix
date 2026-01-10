#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
macOS Dock Icon Utilities for Actifix
-------------------------------------

Ensures a visible dock icon with a gold "AF" on black when running on macOS
with PyObjC available. Safe no-op on other platforms.
"""

from __future__ import annotations

import sys
from typing import Any, Optional


def _is_macos() -> bool:
    """Return True when running on macOS."""
    return sys.platform == "darwin"


def _try_import_appkit():
    """Import AppKit and return the module or None."""
    try:
        import AppKit  # type: ignore
        return AppKit
    except Exception:
        return None


def _create_af_icon(appkit: Any, size: int = 256) -> Optional[Any]:
    """Create a black background icon with gold 'AF' letters."""
    try:
        NSImage = appkit.NSImage
        NSColor = appkit.NSColor
        NSBezierPath = appkit.NSBezierPath
        NSFont = appkit.NSFont
        NSString = getattr(appkit, "NSString", None)
        if NSString is None:
            from Foundation import NSString  # type: ignore
        NSFontAttributeName = appkit.NSFontAttributeName
        NSForegroundColorAttributeName = appkit.NSForegroundColorAttributeName

        image = NSImage.alloc().initWithSize_((size, size))
        image.lockFocus()

        # Background: black
        NSColor.blackColor().set()
        NSBezierPath.bezierPathWithRect_(((0, 0), (size, size))).fill()

        # Text: gold AF
        gold = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.95, 0.78, 0.2, 1.0)
        font = NSFont.boldSystemFontOfSize_(size * 0.55)
        attrs = {NSFontAttributeName: font, NSForegroundColorAttributeName: gold}

        text = NSString.stringWithString_("AF")
        text_size = text.sizeWithAttributes_(attrs)
        x = (size - text_size.width) / 2
        y = (size - text_size.height) / 2
        text.drawAtPoint_withAttributes_((x, y), attrs)

        image.unlockFocus()
        return image
    except Exception:
        return None


def setup_dock_icon() -> bool:
    """
    Ensure a dock icon exists on macOS.

    Returns:
        True if setup ran (and should show an icon), False otherwise.
    """
    if not _is_macos():
        return False

    appkit = _try_import_appkit()
    if not appkit:
        return False

    try:
        app = appkit.NSApplication.sharedApplication()
        app.setActivationPolicy_(appkit.NSApplicationActivationPolicyRegular)

        icon = _create_af_icon(appkit)
        if icon is not None:
            app.setApplicationIconImage_(icon)

        app.activateIgnoringOtherApps_(True)
        return True
    except Exception:
        return False
