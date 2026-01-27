# Design System Action Plan

This document outlines a prioritized, phased approach to improving the Wine Cellar application's design system based on a comprehensive UI/UX critique.

---

## Phase 1: Foundation (High Priority)

### 1.1 Unify Add Bottle Flow

**Problem**: Two conflicting UI patterns exist for adding bottles:
- A dropdown menu with 3 options (`CellarPage.tsx:168-193`)
- A modal with 2 tabs (`AddBottleModal.tsx:87-111`)

**Solution**: Consolidate into a single 3-tab modal pattern.

**Files to Modify**:
- `wine-app/web/src/components/cellar/AddBottleModal.tsx`
- `wine-app/web/src/pages/CellarPage.tsx`

**Implementation**:
```tsx
// AddBottleModal.tsx - Add 'scan' mode
type AddMode = 'search' | 'manual' | 'scan';

// Add third tab:
<button onClick={() => setMode('scan')} className={...}>
  <Camera className="w-4 h-4 inline-block mr-2" />
  Scan Label
</button>
```

**Changes Required**:
1. Add `scan` mode to `AddMode` type in `AddBottleModal.tsx`
2. Add third tab for "Scan Label" with Camera icon
3. Move `ImageUpload` component and scan logic into the modal
4. Remove dropdown menu from `CellarPage.tsx` (lines 159-194)
5. Simplify "+ Add Bottle" to directly open modal

---

### 1.2 Fix Contrast Ratios for Accessibility

**Problem**: Several text elements have insufficient contrast against the cream background (#F5F1E9).

**Files to Modify**:
- `wine-app/web/tailwind.config.js`
- `wine-app/web/src/index.css`

**Elements to Fix**:

| Element | Current | Recommended | Location |
|---------|---------|-------------|----------|
| `text-gray-400` labels | ~#9CA3AF | `text-gray-500` (#6B7280) | Multiple files |
| `text-gray-500` on cream | ~#6B7280 | `text-gray-600` (#4B5563) | Multiple files |
| Unselected star ratings | `text-gray-200` | `text-gray-300` with stroke | `CellarBottleCard.tsx:116-120` |
| Timestamps | Light gray | Darker gray or wine-400 | Chat components |

**Implementation**:
```js
// tailwind.config.js - Add accessible text colors
colors: {
  // ... existing colors
  text: {
    muted: '#6B7280',     // For secondary text on cream (4.5:1 contrast)
    subtle: '#9CA3AF',    // For tertiary text on white only
  }
}
```

**CSS Utility Class**:
```css
/* index.css - Add accessible label class */
.label-mono-accessible {
  @apply font-mono text-xs uppercase tracking-wider text-gray-600;
}
```

---

### 1.3 Standardize Button Hierarchy

**Problem**: Multiple button styles compete visually, creating unclear hierarchy.

**Current Button Variants** (observed):
1. Filled burgundy: "What should I drink tonight?"
2. Outlined white: "+ ADD BOTTLE"
3. Filter chips (selected): "OWNED 3"
4. Filter chips (unselected): "TRIED 1", "SAVED 3"
5. Text buttons: "CONSULT AGENT →"

**Files to Create/Modify**:
- Create: `wine-app/web/src/components/shared/Button.tsx`
- Modify: `wine-app/web/src/index.css`

**Implementation** - Create Button Component:

```tsx
// components/shared/Button.tsx
interface ButtonProps {
  variant: 'primary' | 'secondary' | 'tertiary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
  // ...other props
}

const variants = {
  primary: 'bg-wine-600 text-white hover:bg-wine-700',
  secondary: 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50',
  tertiary: 'bg-cream text-gray-700 hover:bg-cream-dark',
  ghost: 'text-wine-600 hover:text-wine-700 hover:bg-wine-50',
};
```

**Filter Chip Component**:
```tsx
// components/shared/FilterChip.tsx
interface FilterChipProps {
  active: boolean;
  count?: number;
  icon?: React.ReactNode;
  children: React.ReactNode;
}

// Distinct from buttons - rounder, smaller, different interaction
const baseStyles = 'px-4 py-2 rounded-full text-sm font-medium transition-all';
const activeStyles = 'bg-wine-600 text-white';
const inactiveStyles = 'bg-white border border-gray-200 text-gray-600 hover:border-gray-300';
```

---

## Phase 2: Color System (Medium Priority)

### 2.1 Define Semantic Wine Type Colors

**Problem**: Wine type colors are inconsistent across components.

**Current State**:
- `AddBottleModal.tsx:54-67` - Uses `bg-red-100`, `bg-amber-100`, `bg-pink-100`, `bg-yellow-100`
- `CellarBottleCard.tsx:33-46` - Uses `text-red-600`, `text-amber-600`, `text-pink-500`, `text-yellow-600`

**Files to Modify**:
- `wine-app/web/tailwind.config.js`

**Implementation**:
```js
// tailwind.config.js
colors: {
  // ... existing colors
  wineType: {
    red: {
      bg: '#FEE2E2',      // Light red background
      text: '#991B1B',    // Dark red text
      icon: '#DC2626',    // Icon color
    },
    white: {
      bg: '#FEF3C7',      // Light amber background
      text: '#92400E',    // Dark amber text
      icon: '#D97706',    // Icon color
    },
    rose: {
      bg: '#FCE7F3',      // Light pink background
      text: '#9D174D',    // Dark pink text
      icon: '#EC4899',    // Icon color
    },
    sparkling: {
      bg: '#FEF9C3',      // Light yellow background
      text: '#854D0E',    // Dark yellow text
      icon: '#EAB308',    // Icon color (gold)
    },
  },
  status: {
    owned: {
      bg: '#DCFCE7',
      text: '#166534',
    },
    tried: {
      bg: '#DBEAFE',
      text: '#1E40AF',
    },
    saved: {
      bg: '#F3E8FF',
      text: '#7C3AED',
    },
  },
}
```

**Create Helper Utility**:
```tsx
// utils/wineColors.ts
export const getWineTypeColors = (type: string) => ({
  red: { bg: 'bg-wineType-red-bg', text: 'text-wineType-red-text', icon: 'text-wineType-red-icon' },
  white: { bg: 'bg-wineType-white-bg', text: 'text-wineType-white-text', icon: 'text-wineType-white-icon' },
  // ... etc
}[type] || { bg: 'bg-gray-100', text: 'text-gray-700', icon: 'text-gray-500' });
```

---

### 2.2 Standardize Status Badge Colors

**Problem**: Status colors are defined inline and vary between components.

**Files to Modify**:
- `wine-app/web/src/components/cellar/CellarBottleCard.tsx:48-59`
- `wine-app/web/src/components/cellar/CellarList.tsx` (filter chips)

**Implementation**:
Create a shared utility and use the semantic colors defined above.

```tsx
// utils/statusColors.ts
export const getStatusColors = (status: string) => ({
  owned: 'bg-status-owned-bg text-status-owned-text',
  tried: 'bg-status-tried-bg text-status-tried-text',
  wishlist: 'bg-status-saved-bg text-status-saved-text',
  saved: 'bg-status-saved-bg text-status-saved-text',
}[status] || 'bg-gray-100 text-gray-700');
```

---

## Phase 3: Typography Refinement (Medium Priority)

### 3.1 Establish Strict Type Scale

**Files to Modify**:
- `wine-app/web/tailwind.config.js`
- `wine-app/web/src/index.css`

**Implementation**:
```js
// tailwind.config.js
fontSize: {
  'display-xl': ['3rem', { lineHeight: '1.1', letterSpacing: '-0.02em' }],    // 48px - Page titles
  'display-lg': ['2.25rem', { lineHeight: '1.2', letterSpacing: '-0.01em' }], // 36px - Section headers
  'display-md': ['1.5rem', { lineHeight: '1.3' }],                             // 24px - Card titles
  'body-lg': ['1.125rem', { lineHeight: '1.6' }],                              // 18px - Lead text
  'body-md': ['1rem', { lineHeight: '1.5' }],                                  // 16px - Body
  'body-sm': ['0.875rem', { lineHeight: '1.5' }],                              // 14px - Secondary
  'caption': ['0.75rem', { lineHeight: '1.4' }],                               // 12px - Captions
  'label': ['0.625rem', { lineHeight: '1.2', letterSpacing: '0.1em' }],       // 10px - Labels
}
```

**CSS Utility Classes**:
```css
/* index.css */
.text-page-title {
  @apply font-serif italic text-display-xl text-wine-600;
}

.text-section-header {
  @apply font-serif italic text-display-lg text-gray-900;
}

.text-card-title {
  @apply font-serif text-display-md text-gray-900;
}

.text-label {
  @apply font-mono text-label uppercase tracking-widest text-gray-500;
}
```

---

### 3.2 Fix Chat Message Typography

**Problem**: Pip's responses use italic serif which reduces readability in longer messages.

**File to Modify**:
- `wine-app/web/src/components/chat/ChatMessage.tsx`

**Recommendation**: Reserve italic serif for:
- Short, elegant phrases
- Wine names
- Quotations

Use sans-serif for longer explanatory content.

**Implementation**:
```tsx
// ChatMessage.tsx
// Wrap wine names in italic serif, keep explanations in sans
<p className="font-sans text-gray-800">
  I recommend the <span className="font-serif italic">Château Margaux 2015</span>
  for its exceptional balance...
</p>
```

---

## Phase 4: Component Consistency (Medium Priority)

### 4.1 Standardize Card Heights

**Problem**: Wine cards have variable heights due to differing content lengths.

**File to Modify**:
- `wine-app/web/src/components/cellar/CellarBottleCard.tsx`

**Implementation**:
```tsx
// CellarBottleCard.tsx
// Add fixed height sections with proper truncation

<div className="relative bg-white border border-gray-100 rounded-xl overflow-hidden
                hover:shadow-lg transition-all group cursor-pointer
                flex flex-col h-[420px]"> {/* Fixed total height */}

  {/* Wine image area - fixed height */}
  <div className="relative h-48 bg-cream flex-shrink-0 ...">

  {/* Wine info - flex grow with overflow handling */}
  <div className="p-4 flex-1 flex flex-col overflow-hidden">
    {/* Fixed height for name area */}
    <h3 className="font-serif text-lg text-gray-900 line-clamp-2 min-h-[3.5rem]">
      {wineName}
    </h3>

    {/* Producer - single line */}
    <p className="text-sm text-gray-500 truncate">{wineProducer}</p>

    {/* Region - fixed to bottom with auto margin */}
    <p className="font-mono text-[10px] ... mt-auto">{region}</p>
  </div>
</div>
```

---

### 4.2 Improve Star Rating Visibility

**Problem**: Empty star outlines barely visible against cream background.

**File to Modify**:
- `wine-app/web/src/components/cellar/CellarBottleCard.tsx:113-124`
- `wine-app/web/src/pages/WineDetailPage.tsx`

**Implementation**:
```tsx
// Replace text-gray-200 with more visible styling
<Star
  className={`w-3 h-3 ${
    star <= bottle.rating!
      ? 'text-yellow-400 fill-yellow-400'
      : 'text-gray-300 stroke-gray-400'  // More visible outline
  }`}
/>
```

For interactive stars (edit mode), add hover feedback:
```tsx
<Star
  className={`w-7 h-7 transition-all ${
    star <= (editData.rating || 0)
      ? 'text-yellow-400 fill-yellow-400 scale-110'
      : 'text-gray-300 stroke-gray-400 hover:text-yellow-200 hover:scale-105'
  }`}
/>
```

---

### 4.3 Clarify Collection Status Mental Model

**Problem**: Unclear if Owned/Tried/Saved are mutually exclusive or multi-select.

**Files to Analyze**:
- `wine-app/web/src/types/index.ts` - Check `CellarStatus` type
- `wine-app/web/src/components/cellar/CellarBottleCard.tsx:200-218`

**Recommendation**: Based on the current implementation where `status` is a single value (mutually exclusive), update the UI to use a **segmented control** pattern instead of separate buttons:

```tsx
// CellarBottleCard.tsx edit mode
<div className="flex rounded-lg overflow-hidden border border-gray-200">
  {(['owned', 'tried', 'wishlist'] as CellarStatus[]).map((status, index) => (
    <button
      key={status}
      onClick={() => setEditData({ ...editData, status })}
      className={`flex-1 px-3 py-2 font-mono text-[10px] uppercase tracking-wider
                  transition-colors border-r last:border-r-0 border-gray-200
                  ${editData.status === status
                    ? getStatusColor(status)
                    : 'bg-white text-gray-500 hover:bg-gray-50'}`}
    >
      {status === 'wishlist' ? 'saved' : status}
    </button>
  ))}
</div>
```

---

## Phase 5: Spacing & Layout (Low Priority)

### 5.1 Implement 8px Grid System

**File to Modify**:
- `wine-app/web/tailwind.config.js`

**Implementation**:
```js
// tailwind.config.js
spacing: {
  // Override default spacing to enforce 8px grid
  '0': '0',
  '1': '0.25rem',   // 4px (half-step)
  '2': '0.5rem',    // 8px
  '3': '0.75rem',   // 12px (1.5x)
  '4': '1rem',      // 16px (2x)
  '5': '1.25rem',   // 20px (2.5x)
  '6': '1.5rem',    // 24px (3x)
  '8': '2rem',      // 32px (4x)
  '10': '2.5rem',   // 40px (5x)
  '12': '3rem',     // 48px (6x)
  '16': '4rem',     // 64px (8x)
  '20': '5rem',     // 80px (10x)
  '24': '6rem',     // 96px (12x)
}
```

---

### 5.2 Standardize Page Layout

**Create Layout Constants**:
```tsx
// constants/layout.ts
export const LAYOUT = {
  maxWidth: 'max-w-6xl',
  pagePadding: 'px-6 md:px-8',
  sectionSpacing: 'space-y-8',
  cardGap: 'gap-4 md:gap-6',
} as const;
```

---

## Phase 6: Accessibility Improvements (Low Priority)

### 6.1 Add ARIA Labels

**Files to Modify**:
- All interactive components

**Implementation Examples**:
```tsx
// Star rating
<button aria-label={`Rate ${star} out of 5 stars`}>

// Wine type icon
<Wine aria-label={`${wineType} wine`} />

// Status toggle
<div role="radiogroup" aria-label="Collection status">
```

### 6.2 Ensure Touch Target Sizes

**Minimum**: 44x44px for all interactive elements on mobile.

**Files to Audit**:
- `CellarBottleCard.tsx` - Edit/Delete buttons
- Filter chips in `CellarList.tsx`
- Modal close buttons

---

## Implementation Checklist

### Phase 1: Foundation (Week 1)
- [ ] Unify Add Bottle modal with 3 tabs
- [ ] Fix text contrast ratios
- [ ] Create Button component with hierarchy
- [ ] Create FilterChip component

### Phase 2: Color System (Week 1-2)
- [ ] Add wine type colors to Tailwind config
- [ ] Add status colors to Tailwind config
- [ ] Create color utility functions
- [ ] Update all components to use new colors

### Phase 3: Typography (Week 2)
- [ ] Define type scale in Tailwind
- [ ] Create typography utility classes
- [ ] Update page titles and headers
- [ ] Fix chat message typography

### Phase 4: Components (Week 2-3)
- [ ] Standardize card heights
- [ ] Improve star rating visibility
- [ ] Convert status to segmented control
- [ ] Audit and fix all button usages

### Phase 5: Spacing (Week 3)
- [ ] Implement 8px grid
- [ ] Create layout constants
- [ ] Audit and fix spacing inconsistencies

### Phase 6: Accessibility (Week 3-4)
- [ ] Add ARIA labels throughout
- [ ] Ensure touch target sizes
- [ ] Test with screen reader
- [ ] Run Lighthouse accessibility audit

---

## File Summary

| File | Changes |
|------|---------|
| `tailwind.config.js` | Colors, typography, spacing |
| `index.css` | Utility classes, focus styles |
| `AddBottleModal.tsx` | Add scan tab, consolidate flow |
| `CellarPage.tsx` | Remove dropdown, simplify |
| `CellarBottleCard.tsx` | Fixed heights, better stars, segmented control |
| `CellarList.tsx` | Use FilterChip component |
| `ChatMessage.tsx` | Typography refinement |
| **New: `Button.tsx`** | Standardized button component |
| **New: `FilterChip.tsx`** | Distinct filter chip component |
| **New: `utils/wineColors.ts`** | Wine type color helper |
| **New: `utils/statusColors.ts`** | Status color helper |
| **New: `constants/layout.ts`** | Layout constants |

---

## Success Metrics

After implementation, verify:

1. **Accessibility**: Lighthouse score > 95
2. **Contrast**: All text passes WCAG AA (4.5:1)
3. **Consistency**: Single pattern for each UI element type
4. **Touch**: All interactive elements >= 44x44px on mobile
5. **Visual**: Unified color palette with clear hierarchy
