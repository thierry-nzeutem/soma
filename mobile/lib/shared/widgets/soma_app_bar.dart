/// AppBar commun SOMA avec titre et actions optionnelles.
library;

import 'package:flutter/material.dart';

import '../../core/theme/theme_extensions.dart';

class SomaAppBar extends StatelessWidget implements PreferredSizeWidget {
  final String title;
  final List<Widget>? actions;
  final bool showBackButton;
  final Widget? leading;

  const SomaAppBar({
    super.key,
    required this.title,
    this.actions,
    this.showBackButton = false,
    this.leading,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.somaColors;

    return AppBar(
      backgroundColor: colors.navBackground,
      foregroundColor: colors.text,
      elevation: 0,
      centerTitle: true,
      automaticallyImplyLeading: showBackButton,
      leading: leading,
      title: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Logo SOMA — cercle vert menthe
          Container(
            width: 28,
            height: 28,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: LinearGradient(
                colors: [colors.accent, colors.info],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
            ),
            child: const Center(
              child: Text(
                'S',
                style: TextStyle(
                  color: Colors.black,
                  fontSize: 14,
                  fontWeight: FontWeight.w900,
                ),
              ),
            ),
          ),
          const SizedBox(width: 8),
          Text(
            title,
            style: TextStyle(
              color: colors.text,
              fontSize: 18,
              fontWeight: FontWeight.w600,
              letterSpacing: 0.5,
            ),
          ),
        ],
      ),
      actions: actions,
      bottom: PreferredSize(
        preferredSize: const Size.fromHeight(1),
        child: Container(
          height: 1,
          color: colors.border,
        ),
      ),
    );
  }

  @override
  Size get preferredSize => const Size.fromHeight(kToolbarHeight + 1);
}
