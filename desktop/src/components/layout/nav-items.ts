import {
  Activity,
  BarChart3,
  BookOpen,
  Bot,
  Droplets,
  Dumbbell,
  Footprints,
  Heart,
  LayoutDashboard,
  Lightbulb,
  Scale,
  Shield,
  ShieldCheck,
  Trophy,
  UserCircle,
  Utensils,
  Zap,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

export interface NavItem {
  labelKey: string;
  descKey: string;
  href: string;
  icon: LucideIcon;
}

export const NAV_ITEMS: NavItem[] = [
  {
    labelKey: 'nav.dashboard',
    descKey: 'nav.dashboardDesc',
    href: '/dashboard',
    icon: LayoutDashboard,
  },
  {
    labelKey: 'nav.journal',
    descKey: 'nav.journalDesc',
    href: '/journal',
    icon: BookOpen,
  },
  {
    labelKey: 'nav.body',
    descKey: 'nav.bodyDesc',
    href: '/body',
    icon: Scale,
  },
  {
    labelKey: 'nav.workouts',
    descKey: 'nav.workoutsDesc',
    href: '/workouts',
    icon: Dumbbell,
  },
  {
    labelKey: 'nav.nutrition',
    descKey: 'nav.nutritionDesc',
    href: '/nutrition',
    icon: Utensils,
  },
  {
    labelKey: 'nav.hydration',
    descKey: 'nav.hydrationDesc',
    href: '/hydration',
    icon: Droplets,
  },
  {
    labelKey: 'nav.scores',
    descKey: 'nav.scoresDesc',
    href: '/scores',
    icon: Shield,
  },
  {
    labelKey: 'nav.activity',
    descKey: 'nav.activityDesc',
    href: '/activity',
    icon: Footprints,
  },
  {
    labelKey: 'nav.fitness',
    descKey: 'nav.fitnessDesc',
    href: '/fitness',
    icon: Zap,
  },
  {
    labelKey: 'nav.heartRate',
    descKey: 'nav.heartRateDesc',
    href: '/heart-rate',
    icon: Heart,
  },
  {
    labelKey: 'nav.insights',
    descKey: 'nav.insightsDesc',
    href: '/insights',
    icon: Lightbulb,
  },
  {
    labelKey: 'nav.coach',
    descKey: 'nav.coachDesc',
    href: '/coach',
    icon: Bot,
  },
  {
    labelKey: 'nav.analytics',
    descKey: 'nav.analyticsDesc',
    href: '/analytics',
    icon: BarChart3,
  },
  {
    labelKey: 'nav.profile',
    descKey: 'nav.profileDesc',
    href: '/profile',
    icon: UserCircle,
  },
  {
    labelKey: 'nav.hrv',
    descKey: 'nav.hrvDesc',
    href: '/hrv',
    icon: Activity,
  },
  {
    labelKey: 'nav.gamification',
    descKey: 'nav.gamificationDesc',
    href: '/gamification',
    icon: Trophy,
  },
];

/** Primary tabs shown in the mobile bottom bar */
export const PRIMARY_NAV_HREFS = [
  '/dashboard',
  '/nutrition',
  '/workouts',
  '/coach',
  '/profile',
];

export const PRIMARY_NAV = NAV_ITEMS.filter((item) =>
  PRIMARY_NAV_HREFS.includes(item.href)
);

export const SECONDARY_NAV = NAV_ITEMS.filter(
  (item) => !PRIMARY_NAV_HREFS.includes(item.href)
);

export { Activity };

export const ADMIN_NAV: NavItem[] = [
  {
    labelKey: 'nav.admin',
    descKey: 'nav.adminDesc',
    href: '/admin',
    icon: ShieldCheck,
  },
];
export { ShieldCheck };
