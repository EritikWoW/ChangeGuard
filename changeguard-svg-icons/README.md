# ChangeGuard SVG Icons

Included:
- 18 individual SVG files
- `sprite.svg` with all icons as reusable symbols
- `preview.html` to review the icon pack in a browser

Design rules:
- 24x24 viewBox
- transparent background
- stroke-based UI style
- uses `currentColor`

Example:

```html
<img src="icons/dashboard.svg" alt="Dashboard" />
```

Or with the sprite:

```html
<svg width="24" height="24" aria-hidden="true">
  <use href="sprite.svg#dashboard"></use>
</svg>
```
