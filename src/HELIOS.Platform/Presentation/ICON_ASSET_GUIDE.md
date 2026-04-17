# HELIOS Platform - Icon and Asset Generation Guide

## Icon Set Specifications

### Icon Naming Convention

```
helios-[component]-[size]-[state].png
Examples:
- helios-dashboard-64-normal.png
- helios-settings-32-hover.png
- helios-logo-128-dark.png
```

### Icon Sizes (All Variants)

1. **16x16** - Context menu, toolbar
2. **32x32** - Small icons, menu items
3. **64x64** - Tile icons
4. **128x128** - Alt+Tab switcher
5. **256x256** - Settings, about page

### Icon Color Specifications

#### Dark Theme (Recommended Primary)
- Standard Icon: #E6E6E6 (Light Gray)
- Primary Accent: Use current accent color
- Secondary: #B0B0B0 (Medium Gray)
- Disabled: #4A4A4A (Dark Gray)

#### Light Theme
- Standard Icon: #282828 (Dark Gray)
- Primary Accent: Use current accent color
- Secondary: #666666 (Medium Gray)
- Disabled: #D0D0D0 (Light Gray)

### Core Icon Set (24 Base Icons)

**Dashboard & Navigation**
1. `dashboard` - Grid layout, 4 quadrants
2. `settings` - Gear icon
3. `help` - Question mark in circle
4. `notifications` - Bell with notification dot
5. `profile` - User silhouette
6. `logout` - Door with arrow

**System Control**
7. `minimize` - Dash/line
8. `maximize` - Square outline
9. `restore` - Overlapping squares
10. `close` - X or cross
11. `menu` - Three horizontal lines
12. `search` - Magnifying glass

**Actions & Status**
13. `play` - Right-pointing triangle
14. `pause` - Two vertical bars
15. `stop` - Filled square
16. `refresh` - Circular arrows
17. `undo` - Left arrow with hook
18. `redo` - Right arrow with hook

**Status Indicators**
19. `success` - Checkmark in circle
20. `warning` - Triangle with exclamation
21. `error` - Exclamation in circle
22. `info` - Letter 'i' in circle

**Utility**
23. `folder` - Document folder
24. `export` - Arrow exiting box

### Advanced Icons (Optional)

**Theme & Mode**
- `sun` - Light mode indicator
- `moon` - Dark mode indicator
- `theme` - Palette with colors

**Performance**
- `cpu` - Processor unit
- `memory` - RAM stick
- `disk` - Storage icon

**Connectivity**
- `connected` - Network nodes linked
- `disconnected` - Broken network
- `download` - Arrow down to disk
- `upload` - Arrow up from disk

## Splash Screen Specifications

### Dimensions
- **Recommended**: 1920x1080
- **Minimum**: 1280x720
- **Alternative**: 2560x1440 (for 4K displays)
- **Format**: PNG (transparent background recommended)

### Splash Screen Elements

```
┌─────────────────────────────────────────────────────┐
│                                                       │
│                 HELIOS PLATFORM                      │
│                  [Logo Animation]                    │
│                                                       │
│            ████░░░░░░ Loading...  45%               │
│                                                       │
│              Initializing GUI System                │
│                                                       │
└─────────────────────────────────────────────────────┘
```

### Splash Design Guidelines

1. **Background**
   - Dark Theme: Gradient from #141414 to #1E1E1E
   - Light Theme: Gradient from #F5F5F5 to #FFFFFF
   - Animated accent line accent preferred

2. **Logo**
   - Center positioned
   - Size: 256x256 minimum
   - Animated fade-in/scale effect
   - Optional rotating accent border

3. **Text**
   - Font: Modern, clean (Arial, Segoe UI, or sans-serif)
   - "HELIOS PLATFORM" - 48px, bold
   - Status text - 14px, lighter weight
   - Colors: Use theme accent colors

4. **Progress Bar**
   - Width: 400px centered
   - Height: 4px or 8px
   - Color: Current accent color
   - Background: Surface variant color
   - Animation: Linear or smooth curve

5. **Loading Messages** (Optional)
   - "Initializing GUI System..."
   - "Loading theme engine..."
   - "Preparing dashboard..."
   - "Ready for launch"

## Color Icon Usage

For brand/feature icons that use color:

### Blue Accent Icons
- File/document icons (for storage features)
- Database/data icons
- Network/cloud icons
- Color: #0078D7 (light) or #4AC1E0 (dark)

### Purple Accent Icons
- AI/intelligence features
- Advanced settings
- Color: #8E24AA (light) or #BA68C8 (dark)

### Cyan Accent Icons
- Modern/tech features
- Connectivity/sync
- Color: #00BCD4 (light) or #80DEEA (dark)

### Orange Accent Icons
- Performance/gaming
- Warnings/caution (non-critical)
- Energy/power
- Color: #FF9800 (light) or #FFB74D (dark)

### Monochrome Icons
- Use neutral colors for consistency
- Avoid mixing multiple colors in single icon
- Ensure icon remains recognizable at small sizes

## Asset Packaging

### Directory Structure

```
Presentation/Assets/
├── Icons/
│   ├── 16px/
│   │   ├── dark/
│   │   │   ├── helios-dashboard-16.png
│   │   │   └── ... (23 more)
│   │   └── light/
│   │       └── ... (24 icons)
│   ├── 32px/
│   │   ├── dark/
│   │   └── light/
│   ├── 64px/
│   │   ├── dark/
│   │   └── light/
│   ├── 128px/
│   │   ├── dark/
│   │   └── light/
│   └── 256px/
│       ├── dark/
│       └── light/
├── Logo/
│   ├── helios-logo-64.png
│   ├── helios-logo-128.png
│   ├── helios-logo-256.png
│   └── helios-logo-1024.png
├── Splash/
│   ├── splash-1280x720.png
│   ├── splash-1920x1080.png
│   └── splash-2560x1440.png
└── Themes/
    ├── acrylic-overlay.png
    ├── noise-pattern.png
    └── gradient-background.png
```

## PNG Optimization

All icon PNG files should be:
- Optimized with PNGCrush or similar tools
- Interlaced for progressive loading
- Maximum 256 colors (for 16-32px icons)
- 8-bit color depth recommended
- Transparent backgrounds preferred

### File Size Targets
- 16x16: 1-2 KB
- 32x32: 2-4 KB
- 64x64: 4-8 KB
- 128x128: 8-16 KB
- 256x256: 16-32 KB
- Splash: 100-200 KB

## Asset Generation Tools Recommendations

### Icon Creation
- **Figma** - Professional design tool with plugins
- **Adobe Illustrator** - Enterprise standard
- **Inkscape** - Free, open-source vector editor
- **Icon Forge** - Specialized icon creation tool

### Batch Processing
- **ImageMagick** - Command-line image manipulation
- **FFmpeg** - Media processing
- **Aseprite** - Pixel art and animation
- **TexturePacker** - Atlas generation

### Example ImageMagick Commands

```bash
# Convert SVG to PNG at multiple sizes
for size in 16 32 64 128 256; do
  convert icon.svg -resize ${size}x${size} icon-${size}.png
done

# Optimize PNG
pngcrush -brute icon.png icon-optimized.png

# Create icon with white outline (dark theme)
convert icon.png -bordercolor white -border 1 icon-outlined.png
```

## Accessibility Requirements

### Icon Design Principles
1. **Recognizable** - Icon should be clear at smallest size (16x16)
2. **Consistent** - Maintain uniform stroke width and style
3. **Distinct** - Different from other icons in set
4. **Meaningful** - Aligns with common conventions

### Testing Icon Readability
- View at actual displayed sizes
- Test on both light and dark backgrounds
- Verify color blind safe (avoid red-green only)
- Check screen reader text availability
- Validate 3:1 contrast ratio minimum

### SVG Guidelines (If Using SVG Icons)

```xml
<!-- Template for HELIOS SVG Icon -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <title>Dashboard Icon</title>
  <desc>Navigation icon for main dashboard</desc>
  <!-- Icon content here -->
  <path fill="currentColor" d="..." />
</svg>
```

## Animation Guidelines

### Splash Screen Animation

**Recommended Sequence (3 seconds):**
1. 0-0.5s: Logo fade-in + scale
2. 0.5-2.5s: Loading progress (linear or ease-out)
3. 2.5-3s: Status text update
4. 3s: Fade to main window

### Icon Hover States

- **Scale**: +10% for 150ms (EaseOutQuad)
- **Opacity**: To 0.8 if disabled state
- **Color**: Shift to secondary color if color icon

### Animated Icons

- **Loading spinner** - Infinite rotation (1.5-2s per rotation)
- **Pulse effect** - Success/warning icons (1-2s pulse cycle)
- **Slide animation** - Transitioning between states

## Integration with GUI System

### Using Icons in Controls

```csharp
using HELIOS.Platform.Presentation.Controls;
using HELIOS.Platform.Presentation.Services;

// In your code
var guiService = new GUIDashboardService();

// Navigation with icons
var navControl = new NavControl();
navControl.AddItem("dashboard", "Dashboard", "dash");
navControl.AddItem("settings", "Settings", "settings");
navControl.AddItem("help", "Help", "help");

// Button with icon
var button = new ModernButton("Apply");
// Icon would be set through XAML/UI binding in WinUI 3 implementation
```

## Asset Delivery Checklist

- [ ] All 24 base icons created (16-256px)
- [ ] Dark theme variants tested
- [ ] Light theme variants tested
- [ ] High contrast mode verified
- [ ] PNG optimized (file sizes within targets)
- [ ] Splash screens (1280x720, 1920x1080, 2560x1440)
- [ ] Logo assets at standard sizes
- [ ] SVG source files (if applicable)
- [ ] Color blind mode tested
- [ ] Accessibility labels provided

## Version Control

Assets should be tracked in git with:
```
.gitattributes (include binary files for proper diff)
Presentation/Assets/Icons/  # Directory structure as above
Presentation/Assets/Logo/
Presentation/Assets/Splash/
```

---

**Last Updated**: 2024 | **Version**: 1.0.0
