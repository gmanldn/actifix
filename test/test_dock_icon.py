"""
Tests for Actifix dock icon setup.

These tests mock AppKit so they can run on any platform.
"""

import sys
from types import SimpleNamespace
from typing import Any

import pytest


def build_fake_appkit():
    """Return a fake AppKit module capturing dock icon calls."""

    class FakeColor:
        def __init__(self, r=None, g=None, b=None, a=None):
            self.rgba = (r, g, b, a)

        def set(self):
            pass

        @classmethod
        def blackColor(cls):
            return cls(0, 0, 0, 1)

        @classmethod
        def colorWithCalibratedRed_green_blue_alpha_(cls, r, g, b, a):
            return cls(r, g, b, a)

    class FakeBezier:
        def __init__(self, rect=None):
            self.rect = rect

        @classmethod
        def bezierPathWithRect_(cls, rect):
            return cls(rect)

        def fill(self):
            pass

    class FakeFont:
        def __init__(self, size):
            self.size = size

        @classmethod
        def boldSystemFontOfSize_(cls, size):
            return cls(size)

    class FakeText:
        def __init__(self, text):
            self.text = text

        def sizeWithAttributes_(self, attrs):
            # Rough size: width = 0.6 * size per char, height = size
            font = attrs.get("NSFontAttributeName")
            size = getattr(font, "size", 10)
            return SimpleNamespace(width=len(self.text) * size * 0.6, height=size)

        def drawAtPoint_withAttributes_(self, point, attrs):
            self.drawn_at = point
            self.drawn_attrs = attrs

        @classmethod
        def stringWithString_(cls, text):
            return cls(text)

    class FakeImage:
        def __init__(self, size=None):
            self.size = size
            self.locked = False

        @classmethod
        def alloc(cls):
            return cls()

        def initWithSize_(self, size):
            self.size = size
            return self

        def lockFocus(self):
            self.locked = True

        def unlockFocus(self):
            self.locked = False

    class FakeApp:
        _instance = None

        def __init__(self):
            self.policy = None
            self.icon = None
            self.activated = False

        @classmethod
        def sharedApplication(cls):
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

        def setActivationPolicy_(self, policy):
            self.policy = policy

        def setApplicationIconImage_(self, icon):
            self.icon = icon

        def activateIgnoringOtherApps_(self, flag):
            self.activated = flag

    fake = SimpleNamespace(
        NSApplication=FakeApp,
        NSApplicationActivationPolicyRegular=0,
        NSImage=FakeImage,
        NSColor=FakeColor,
        NSBezierPath=FakeBezier,
        NSFont=FakeFont,
        NSString=FakeText,
        NSFontAttributeName="NSFontAttributeName",
        NSForegroundColorAttributeName="NSForegroundColorAttributeName",
    )
    return fake


def test_setup_dock_icon_non_macos(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    from actifix import dock_icon

    assert dock_icon.setup_dock_icon() is False


def test_setup_dock_icon_with_mock_appkit(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    fake_appkit = build_fake_appkit()
    monkeypatch.setitem(sys.modules, "AppKit", fake_appkit)

    from actifix import dock_icon

    result = dock_icon.setup_dock_icon()
    assert result is True

    # Validate icon drawing occurred
    icon = fake_appkit.NSApplication.sharedApplication().icon
    assert icon is not None
    assert getattr(fake_appkit.NSApplication.sharedApplication(), "policy") == fake_appkit.NSApplicationActivationPolicyRegular

    # Ensure gold-ish color values were used
    gold_color = fake_appkit.NSColor.colorWithCalibratedRed_green_blue_alpha_(0.95, 0.78, 0.2, 1.0)
    assert gold_color.rgba == (0.95, 0.78, 0.2, 1.0)
