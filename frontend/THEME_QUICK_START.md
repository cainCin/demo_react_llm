# Theme System - Quick Start Guide

## 🎨 What is the Theme System?

The theme system allows you to:
- Switch between multiple color themes
- Easily add new themes from the internet
- Maintain consistent styling across the app
- Persist theme selection in browser

## 🚀 Quick Usage

### For Users
1. Click the 🎨 theme switcher in the header
2. Select a theme from the dropdown
3. Theme is saved automatically

### For Developers

#### Adding a New Theme (5 minutes)

1. **Open** `frontend/src/themes/themes.js`

2. **Copy an existing theme** (e.g., `light`)

3. **Modify colors**:
```javascript
myTheme: {
  name: 'My Theme',
  colors: {
    primary: '#your-color',
    background: '#ffffff',
    // ... copy from existing theme
  }
}
```

4. **Get colors from online tools**:
   - [Coolors.co](https://coolors.co/) - Generate palettes
   - [Material Design](https://material.io/resources/color/) - Material colors
   - [Adobe Color](https://color.adobe.com/) - Color harmonies

5. **Done!** Theme appears automatically in switcher

#### Using Theme in Components

```jsx
import { useTheme } from './contexts/ThemeContext'

function MyComponent() {
  const { currentTheme } = useTheme()
  const primaryColor = currentTheme.colors.primary
  
  return <div style={{ color: primaryColor }}>Hello</div>
}
```

#### Using Theme in CSS

```css
.my-class {
  color: var(--color-text, #333);
  background: var(--color-background, #fff);
}
```

## 📋 Available Themes

- **Light** - Default light theme
- **Dark** - Dark mode
- **Ocean** - Blue/teal theme
- **Forest** - Green theme
- **Sunset** - Orange/red theme
- **Purple Dream** - Purple theme

## 🔧 File Structure

```
frontend/src/
├── themes/
│   ├── themes.js          # Theme definitions
│   └── README.md          # Full documentation
├── contexts/
│   └── ThemeContext.jsx   # Theme provider
├── components/
│   ├── ThemeSwitcher.jsx  # Theme switcher UI
│   └── ThemeSwitcher.css  # Switcher styles
└── App.css                # Uses CSS variables
```

## 💡 Tips

1. **Test all themes** - Make sure your component works in dark mode
2. **Use CSS variables** - Never hardcode colors
3. **Check contrast** - Ensure text is readable
4. **Consistent naming** - Use standard color property names

## 📚 Full Documentation

See `frontend/src/themes/README.md` for complete documentation.

