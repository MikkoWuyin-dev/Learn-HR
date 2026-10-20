# wakeout.app — extracted evidence

CSS 77.3 kB · 15 pages · 27931 class tokens

## Semantic brand tokens (from :root)
- `--color-muted-foreground: var(--muted-foreground)`
- `--color-ink: #043629`
- `--color-ink-deep: #00261c`
- `--color-paper: #fff8e6`
- `--color-cream: #fff8e6`
- `--color-lime: #68be00`
- `--color-lime-deep: #498500`
- `--color-pink: #f66f8e`
- `--color-purple: #8a38f5`
- `--color-orange: #ff8300`
- `--color-orange-soft: #ffe7d2`
- `--color-cyan: #00b6d2`
- `--color-cyan-deep: #0e8ca6`
- `--color-sky: #84d2f6`
- `--color-yellow: #ffc629`
- `--color-sun: #ffc300`
- `--color-ember: #ff6b3e`
- `--color-ember-deep: #c7431d`
- `--color-sunrise: #ffe7d2`
- `--color-ink-morning: #5c2e0e`
- `--color-dusk: #331c45`
- `--color-plum: #592043`
- `--color-red: #e5484d`

## shadcn-style aliases
- `--radius: 1.25rem`
- `--background: #fff8e6`
- `--foreground: #043629`
- `--card: #fff`
- `--card-foreground: #043629`
- `--popover: #fff`
- `--popover-foreground: #043629`
- `--primary: #68be00`
- `--primary-foreground: #043629`
- `--secondary: #f66f8e`
- `--secondary-foreground: #043629`
- `--muted: #f3ead3`
- `--muted-foreground: #3f5c52`
- `--accent: #8a38f5`
- `--accent-foreground: #fff8e6`
- `--destructive: #e5484d`
- `--border: #043629`
- `--input: #043629`
- `--ring: #8a38f5`
- `--chart-1: #68be00`
- `--chart-2: #f66f8e`
- `--chart-3: #8a38f5`
- `--chart-4: #ff8300`
- `--chart-5: #00b6d2`
- `--sidebar: #fff8e6`
- `--sidebar-foreground: #043629`
- `--sidebar-primary: #68be00`
- `--sidebar-primary-foreground: #043629`
- `--sidebar-accent: #f66f8e`
- `--sidebar-accent-foreground: #043629`
- `--sidebar-border: #043629`
- `--sidebar-ring: #8a38f5`

## Fonts
- Fredoka w400 normal display:swap
- Fredoka w500 normal display:swap
- Fredoka w600 normal display:swap
- Fredoka w700 normal display:swap
- Fredoka Fallback w  display:
- Space Grotesk w300 700 normal display:swap
- Space Grotesk Fallback w  display:

## Keyframes
- **wiggle**: `0%,to{transform:rotate(-3deg)}50%{transform:rotate(3deg)}`
- **wobble**: `0%,to{transform:translateY(0)rotate(0)}25%{transform:translateY(-6px)rotate(-2deg)}75%{transform:translateY(-2px)rotate(2deg)}`
- **spin-slow**: `to{transform:rotate(360deg)}`
- **float**: `0%,to{transform:translateY(0)}50%{transform:translateY(-10px)}`
- **notif-pop**: `0%,70%,to{transform:rotate(-1deg)scale(1)}4%{transform:rotate(-3deg)scale(.94)}10%{transform:rotate(2deg)scale(1.08)}16%{transform:rotate(-1deg)scale(1)}`
- **shape-burst**: `0%,75%,to{opacity:0;transform:scale(0)translate(0)}8%{opacity:0;transform:scale(.2)translate(0)}14%{transform:scale(1.25)translate(calc(var(--burst-x,0px)*.5),calc(var(--burst-y,0px)*.5));opacity:1}40%{transform:scale(1)translate(var(--burst-x,0px),var(--burst-y,0px))rotate(var(--burst-rot,0deg));op`

## border-radius values in CSS
- `0` ×2
- `.25rem` ×1
- `2.25rem` ×1
- `3rem` ×1
- `1px` ×1
- `2.5rem` ×1
- `2rem` ×1
- `3px` ×1
- `21%/17%` ×1
- `26%/21%` ×1
- `40px` ×1
- `3.40282e38px` ×1
- `1.25rem` ×1
- `.5rem` ×1
- `1.75rem` ×1

## box-shadow values in CSS
- `var(--tw-inset-shadow),var(--tw-inset-ring-shadow),var(--tw-ring-offset-shadow),var(--tw-ring-shadow),var(--tw-shadow)` ×3
- `none` ×1
- `6px 6px 0 0 var(--color-ink)` ×1
- `3px 3px 0 0 var(--color-ink)` ×1
- `10px 10px 0 0 var(--color-ink)` ×1
- `6px 6px 0 0 var(--color-pink)` ×1
- `6px 6px 0 0 var(--color-purple)` ×1
- `6px 6px 0 0 var(--color-lime)` ×1

## letter-spacing / text-transform / font-weight
- letterSpacing: `inherit`×2, `-.02em`×2, `.2em`×1, `.3em`×1, `.18em`×1, `.25em`×1, `.35em`×1, `var(--tracking-tight)`×1, `var(--tracking-wide)`×1, `var(--tracking-wider)`×1, `var(--tracking-widest)`×1, `-.01em`×1
- textTransform: `lowercase`×1, `uppercase`×1
- fontWeight: `700`×6, `500`×4, `400`×3, `600`×3, `300 700`×3, `bolder`×2, `inherit`×1, `var(--font-weight-black)`×1, `var(--font-weight-bold)`×1, `var(--font-weight-extrabold)`×1, `var(--font-weight-medium)`×1, `var(--font-weight-normal)`×1, `var(--font-weight-semibold)`×1

## animation / transition
- animation: `12s linear infinite spin-slow`×2, `.9s ease-in-out infinite wiggle`×2, `5s ease-in-out infinite float`×1, `5s ease-in-out infinite notif-pop`×1, `5s ease-in-out infinite shape-burst`×1, `3s ease-in-out infinite wobble`×1
- transitionDuration: `var(--tw-duration,var(--default-transition-duration))`×6, `.15s`×1, `.3s`×1

## most-used literal colors in CSS
- `color-mix(in lab, red, red)` ×60
- `#0000` ×21
- `color-mix(in oklab,var(--color-ink)` ×18
- `color-mix(in oklab,var(--color-white)` ×16
- `#043629` ×14
- `color-mix(in oklab,var(--color-paper)` ×7
- `color-mix(in oklab,var(--color-black)` ×6
- `color-mix(in oklab,var(--color-stage)` ×6
- `#fff` ×5
- `#fff8e6` ×5
- `#8a38f5` ×5
- `#0000001a` ×5
- `#68be00` ×4
- `#f66f8e` ×4
- `#3a1c05` ×4
- `#ffe7d2` ×3
- `color-mix(in oklab,var(--color-lime)` ×3
- `#ff8300` ×2
- `#00b6d2` ×2
- `#331c45` ×2
- `#e5484d` ×2
- `#04362933` ×2
- `#0436294d` ×2
- `#04362966` ×2
- `#ffffff0d` ×2
- `#ffffff1a` ×2
- `#fff3` ×2
- `#0f0f0f` ×2
- `#1a1a1a` ×2
- `#2a2a2a` ×2

## top utility classes in shipped HTML
- `font-display` ×773
- `border-[var(--color-ink)]` ×720
- `text-sm` ×693
- `flex` ×636
- `items-center` ×628
- `absolute` ×573
- `border-[3px]` ×517
- `font-bold` ×512
- `font-medium` ×491
- `relative` ×480
- `rounded-full` ×442
- `uppercase` ×383
- `hover:text-[var(--color-purple)]` ×379
- `transition-transform` ×364
- `text-[var(--color-ink)]` ×327
- `shadow-sticker` ×324
- `leading-tight` ×303
- `justify-center` ×294
- `gap-2` ×293
- `hover:-rotate-1` ×280
- `text-lg` ×279
- `leading-relaxed` ×272
- `tracking-widest` ×255
- `overflow-hidden` ×238
- `bg-[var(--color-paper)]` ×232
- `text-xs` ×225
- `rounded-3xl` ×220
- `mx-auto` ×220
- `rounded-2xl` ×216
- `inline-flex` ×212
- `inline-block` ×210
- `flex-col` ×195
- `w-full` ×187
- `font-semibold` ×183
- `shadow-sticker-sm` ×179
- `text-base` ×176
- `h-4` ×176
- `text-xl` ×171
- `px-6` ×167
- `px-3` ×166
- `w-4` ×166
- `pointer-events-none` ×161
- `mb-4` ×161
- `inset-0` ×152
- `text-[10px]` ×142
- `object-cover` ×138
- `text-[var(--color-paper)]` ×136
- `mb-2` ×135
- `border` ×134
- `py-1` ×132

## bg-* usage
- `bg-[var(--color-paper)]` ×232
- `bg-[var(--color-ink)]` ×115
- `bg-[var(--color-lime)]` ×106
- `bg-[var(--color-pink)]` ×69
- `bg-black` ×65
- `bg-[var(--color-stage)]` ×63
- `bg-gradient-to-t` ×53
- `bg-white/10` ×37
- `bg-white/5` ×25
- `bg-[var(--color-yellow)]` ×22
- `bg-[var(--color-cyan)]` ×21
- `bg-white/90` ×20
- `bg-[#1a1a1a]` ×15
- `bg-[#2a2a2a]` ×13
- `bg-[var(--color-paper)]/95` ×12
- `bg-[var(--color-ember)]` ×10
- `bg-white/20` ×8
- `bg-[var(--color-ink)]/30` ×6
- `bg-[var(--color-lime)]/15` ×5
- `bg-[var(--color-purple)]` ×5
- `bg-[#ff5f57]` ×5
- `bg-[#febc2e]` ×5
- `bg-[#28c840]` ×5
- `bg-[#0f0f0f]` ×5
- `bg-[#043629]` ×5
- `bg-energy` ×5
- `bg-sunrise` ×4
- `bg-gradient-to-b` ×4
- `bg-[var(--color-sky)]` ×4
- `bg-no-repeat` ×2
- `bg-[var(--color-paper)]/25` ×2
- `bg-dusk` ×2
- `bg-[var(--color-plum)]` ×2
- `bg-dots` ×2
- `bg-[var(--color-pink)]/90` ×1
- `bg-black/40` ×1
- `bg-[#111]` ×1

## text size usage
- `text-sm` ×693
- `text-lg` ×279
- `text-xs` ×225
- `text-base` ×176
- `text-xl` ×171
- `text-4xl` ×100
- `text-2xl` ×99
- `text-5xl` ×29
- `text-3xl` ×19
- `text-6xl` ×4

## radius / shadow / border usage
- radius: `relative`×480 `rounded-full`×442 `rounded-3xl`×220 `rounded-2xl`×216 `rotate-1`×83 `right-0`×56 `rotate-12`×55 `right-3`×31 `right-10`×26 `rotate-6`×24 `right-[8%]`×20 `rounded`×17 `rotate-[0.5deg]`×16 `rotate-2`×15 `rounded-t-lg`×13 `rotate-[8deg]`×12 `right-16`×12 `rounded-sm`×12 `rounded-[26%/21%]`×10 `rounded-[21%/17%]`×10 `rounded-r-lg`×10 `rounded-r-md`×10
- shadow: `shadow-sticker`×324 `shadow-sticker-sm`×179 `shadow-sticker-lg`×77
- border: `border-[var(--color-ink)]`×720 `border-[3px]`×517 `border-t-[3px]`×68 `border-[var(--color-ink)]/20`×63 `border-[4px]`×62 `border-b-[3px]`×50 `border-[2px]`×44 `border-dashed`×41 `border-t-2`×40 `border-[var(--color-ink)]/30`×40 `border-[var(--color-ink)]/10`×40 `border-2`×37 `border-[var(--color-paper)]`×34 `border-y-[3px]`×30 `border-[var(--color-paper)]/20`×30 `border-white/20`×30 `border-t`×30 `border-white/10`×26 `border-current`×18 `border-t-[2px]`×15 `border-[var(--color-ink)]/15`×15 `border-black/20`×15
- gap: `gap-2`×293 `gap-1.5`×80 `gap-4`×57 `gap-3`×49 `gap-1`×40 `gap-10`×30 `gap-6`×26 `gap-12`×25 `gap-2.5`×17 `gap-5`×17 `gap-x-3`×14 `gap-y-1`×14 `gap-7`×12 `gap-8`×3 `gap-14`×1
- spacing: `mx-auto`×220 `px-6`×167 `px-3`×166 `mb-4`×161 `mb-2`×135 `py-1`×132 `py-3`×128 `px-4`×126 `p-6`×119 `mb-1`×113 `mb-3`×104 `mb-6`×93 `py-2`×77 `p-4`×76 `px-2`×76 `py-1.5`×60 `p-5`×53 `py-24`×51 `mt-3`×47 `mb-5`×47 `mt-4`×42 `pt-4`×35

## font-* usage
- `font-display` ×773
- `font-bold` ×512
- `font-medium` ×491
- `text-[var(--color-ink)]` ×327
- `font-semibold` ×183
- `text-[10px]` ×142
- `text-[var(--color-paper)]` ×136
- `text-[var(--color-muted-foreground)]` ×132
- `text-[var(--color-ink)]/70` ×108
- `text-[11px]` ×95
- `text-[var(--color-ink)]/80` ×90
- `text-[var(--color-ink)]/85` ×87
- `text-[var(--color-paper)]/80` ×59
- `text-[var(--color-ink)]/75` ×54
- `text-[var(--color-purple)]` ×44
- `text-[var(--color-ink)]/60` ×42
- `text-[var(--color-ember)]` ×29
- `text-[var(--color-lime)]` ×27
- `font-normal` ×22
- `text-[12px]` ×22
- `text-[var(--color-pink)]` ×20
- `text-[var(--color-lime-deep)]` ×18
- `font-body` ×15
- `font-app-ui` ×14
- `text-[9px]` ×14