# Theme System Documentation

## Overview

The theme system provides a consistent, maintainable way to style the application. It uses CSS variables and React Context to enable dynamic theme switching and easy theme customization.

## Architecture

### Components

1. **`themes.js`** - Theme definitions (color palettes, gradients)
2. **`ThemeContext.jsx`** - React context for theme management
3. **`ThemeSwitcher.jsx`** - UI component for switching themes
4. **CSS Variables** - Applied to `:root` for global access

### How It Works

1. Themes are defined in `themes.js` as JavaScript objects
2. `ThemeProvider` wraps the app and applies CSS variables to `:root`
3. All CSS uses CSS variables instead of hardcoded colors
4. Theme selection is persisted in `localStorage`
5. Users can switch themes via the `ThemeSwitcher` component

## Adding a New Theme

### Step 1: Define the Theme

Add a new theme object to `themes.js`:

```javascript
export const themes = {
  // ... existing themes ...
  
  myNewTheme: {
    name: 'My New Theme',
    colors: {
      // Primary colors
      primary: '#your-color',
      primaryDark: '#your-dark-color',
      primaryLight: '#your-light-color',
      
      // Background colors
      background: '#ffffff',
      backgroundSecondary: '#f8f9fa',
      backgroundTertiary: '#f5f5f5',
      
      // Text colors
      text: '#333333',
      textSecondary: '#666666',
      textTertiary: '#999999',
      textInverse: '#ffffff',
      
      // ... (copy structure from existing theme)
    },
    gradients: {
      header: 'linear-gradient(135deg, #color1 0%, #color2 100%)',
      primary: 'linear-gradient(135deg, #color1 0%, #color2 100%)',
    }
  }
}
```

### Step 2: Use Online Theme Generators

You can use online tools to generate color palettes:

1. **Coolors.co** - https://coolors.co/
   - Generate color palettes
   - Export as CSS variables
   - Copy colors to your theme

2. **Material Design Color Tool** - https://material.io/resources/color/
   - Generate Material Design color schemes
   - Get primary, secondary, and accent colors

3. **Adobe Color** - https://color.adobe.com/
   - Create color harmonies
   - Export color values

4. **UI Colors** - https://uicolors.app/create
   - Generate UI color palettes
   - Get shades and tints automatically

### Step 3: Convert to Theme Format

When you get colors from online tools, map them to our theme structure:

```javascript
// Example: Material Design theme
materialBlue: {
  name: 'Material Blue',
  colors: {
    primary: '#2196F3',        // Primary 500
    primaryDark: '#1976D2',    // Primary 700
    primaryLight: '#64B5F6',   // Primary 300
    background: '#FFFFFF',
    backgroundSecondary: '#F5F5F5',
    // ... etc
  }
}
```

## Theme Structure

### Required Color Properties

All themes must include these color properties:

#### Primary Colors
- `primary` - Main brand color
- `primaryDark` - Darker variant
- `primaryLight` - Lighter variant

#### Background Colors
- `background` - Main background
- `backgroundSecondary` - Secondary background (messages area)
- `backgroundTertiary` - Tertiary background (inputs, hover states)

#### Text Colors
- `text` - Primary text color
- `textSecondary` - Secondary text (muted)
- `textTertiary` - Tertiary text (very muted)
- `textInverse` - Text on colored backgrounds

#### Border Colors
- `border` - Standard border
- `borderLight` - Light border
- `borderDark` - Dark border

#### Status Colors
- `success` - Success state (green)
- `error` - Error state (red)
- `warning` - Warning state (yellow/orange)
- `info` - Info state (blue)

#### Message Colors
- `messageUserBg` - User message background (gradient)
- `messageUserText` - User message text
- `messageAssistantBg` - Assistant message background
- `messageAssistantText` - Assistant message text

#### Input Colors
- `inputBg` - Input background
- `inputBorder` - Input border
- `inputBorderFocus` - Input border when focused
- `inputText` - Input text color

#### Button Colors
- `buttonPrimary` - Primary button background (gradient)
- `buttonPrimaryHover` - Primary button hover state
- `buttonText` - Button text color

#### Shadow Colors
- `shadow` - Standard shadow
- `shadowLight` - Light shadow
- `shadowHover` - Hover shadow

### Gradients

- `header` - Header background gradient
- `primary` - Primary gradient (buttons, etc.)

## Using Themes in Components

### Access Theme in React Components

```jsx
import { useTheme } from '../contexts/ThemeContext'

function MyComponent() {
  const { currentTheme, currentThemeName, setTheme } = useTheme()
  
  // Access theme colors
  const primaryColor = currentTheme.colors.primary
  
  // Change theme
  setTheme('dark')
  
  return <div style={{ color: primaryColor }}>Hello</div>
}
```

### Using CSS Variables

CSS variables are automatically applied to `:root`. Use them in your CSS:

```css
.my-element {
  background: var(--color-background, #ffffff);
  color: var(--color-text, #333333);
  border: 1px solid var(--color-border, #e0e0e0);
}
```

The second parameter is a fallback value (used if variable is not defined).

## Best Practices

1. **Always use CSS variables** - Never hardcode colors in CSS
2. **Provide fallbacks** - Always include fallback values in `var()`
3. **Test all themes** - Ensure your component looks good in all themes
4. **Consistent naming** - Use the standard color property names
5. **Accessibility** - Ensure sufficient contrast ratios (WCAG AA minimum)

## Theme Examples from Internet

### Example 1: GitHub Dark Theme

```javascript
githubDark: {
  name: 'GitHub Dark',
  colors: {
    primary: '#58a6ff',
    background: '#0d1117',
    backgroundSecondary: '#161b22',
    text: '#c9d1d9',
    // ... etc
  }
}
```

### Example 2: Dracula Theme

```javascript
dracula: {
  name: 'Dracula',
  colors: {
    primary: '#bd93f9',
    background: '#282a36',
    backgroundSecondary: '#44475a',
    text: '#f8f8f2',
    // ... etc
  }
}
```

### Example 3: Nord Theme

```javascript
nord: {
  name: 'Nord',
  colors: {
    primary: '#88c0d0',
    background: '#2e3440',
    backgroundSecondary: '#3b4252',
    text: '#eceff4',
    // ... etc
  }
}
```

## Troubleshooting

### Theme not applying?
- Check browser console for CSS variable errors
- Verify theme name exists in `themes.js`
- Clear localStorage and reload

### Colors look wrong?
- Ensure all required color properties are defined
- Check CSS variable names match (case-sensitive)
- Verify fallback values are appropriate

### Theme switcher not showing?
- Ensure `ThemeProvider` wraps your app in `main.jsx`
- Check `ThemeSwitcher` is imported and rendered

## Resources

- [CSS Variables Guide](https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties)
- [Color Palette Generators](https://coolors.co/)
- [Material Design Colors](https://material.io/design/color/the-color-system.html)
- [WCAG Contrast Checker](https://webaim.org/resources/contrastchecker/)

