/// Modèle ExerciseFrame — résultat d'analyse d'un frame (LOT 7).
///
/// Contient les angles calculés à partir de la pose détectée.
/// Chaque exercice utilise un sous-ensemble des angles disponibles.
library;

// ── Exercices supportés ───────────────────────────────────────────────────────

/// Exercices supportés en V1 Computer Vision SOMA.
enum SupportedExercise {
  squat(
    nameEn: 'Squat',
    nameFr: 'Squat',
    cameraGuide: 'Placez-vous de profil à 2-3m de la caméra.',
    isTimerBased: false,
    targetReps: 10,
  ),
  pushUp(
    nameEn: 'Push-up',
    nameFr: 'Pompe',
    cameraGuide: 'Placez-vous de côté, corps horizontal. Caméra au sol.',
    isTimerBased: false,
    targetReps: 10,
  ),
  plank(
    nameEn: 'Plank',
    nameFr: 'Planche',
    cameraGuide: 'Placez-vous de côté, corps horizontal. Caméra au sol.',
    isTimerBased: true,
    targetReps: 0,
  ),
  jumpingJack(
    nameEn: 'Jumping Jack',
    nameFr: 'Jumping Jack',
    cameraGuide: 'Placez-vous face à la caméra à 2-3m de distance.',
    isTimerBased: false,
    targetReps: 20,
  ),
  lunge(
    nameEn: 'Lunge',
    nameFr: 'Fente avant',
    cameraGuide: 'Placez-vous de profil à 2-3m de la caméra.',
    isTimerBased: false,
    targetReps: 10,
  ),
  sitUp(
    nameEn: 'Sit-up',
    nameFr: 'Abdominal',
    cameraGuide:
        'Allongez-vous sur le dos, caméra de côté au niveau du sol.',
    isTimerBased: false,
    targetReps: 15,
  );

  final String nameEn;
  final String nameFr;
  final String cameraGuide;
  final bool isTimerBased;
  final int targetReps;

  const SupportedExercise({
    required this.nameEn,
    required this.nameFr,
    required this.cameraGuide,
    required this.isTimerBased,
    required this.targetReps,
  });
}

// ── Angles articulaires ───────────────────────────────────────────────────────

/// Angles articulaires calculés pour un frame donné.
///
/// Angles en degrés. Null si les landmarks requis sont absents ou peu fiables.
class ExerciseAngles {
  // ── Jambes / Bas du corps ──────────────────────────────────────────────
  /// Angle genou (hanche–genou–cheville). Squat, Lunge.
  final double? leftKneeAngle;
  final double? rightKneeAngle;

  /// Angle hanche (épaule–hanche–genou). Sit-up.
  final double? leftHipAngle;
  final double? rightHipAngle;

  // ── Bras / Haut du corps ───────────────────────────────────────────────
  /// Angle coude (épaule–coude–poignet). Push-up.
  final double? leftElbowAngle;
  final double? rightElbowAngle;

  // ── Corps global ────────────────────────────────────────────────────────
  /// Alignement corps (épaule–hanche–cheville). Plank, Push-up.
  final double? bodyAlignmentAngle;

  // ── Jumping Jack ───────────────────────────────────────────────────────
  /// Rapport ouverture bras (0=fermé, 1=complètement ouvert).
  final double? armSpreadRatio;

  /// Rapport ouverture jambes (0=fermé, 1=complètement ouvert).
  final double? legSpreadRatio;

  const ExerciseAngles({
    this.leftKneeAngle,
    this.rightKneeAngle,
    this.leftHipAngle,
    this.rightHipAngle,
    this.leftElbowAngle,
    this.rightElbowAngle,
    this.bodyAlignmentAngle,
    this.armSpreadRatio,
    this.legSpreadRatio,
  });

  static const ExerciseAngles empty = ExerciseAngles();

  // ── Helpers : moyennes gauche/droite ──────────────────────────────────

  /// Angle genou moyen (préfère le côté le plus fiable).
  double? get kneeAngle => _avg(leftKneeAngle, rightKneeAngle);

  /// Angle hanche moyen.
  double? get hipAngle => _avg(leftHipAngle, rightHipAngle);

  /// Angle coude moyen.
  double? get elbowAngle => _avg(leftElbowAngle, rightElbowAngle);

  static double? _avg(double? a, double? b) {
    if (a == null && b == null) return null;
    if (a == null) return b;
    if (b == null) return a;
    return (a + b) / 2.0;
  }
}

// ── Frame d'analyse ───────────────────────────────────────────────────────────

/// Résultat complet de l'analyse d'un frame.
class ExerciseFrame {
  final ExerciseAngles angles;
  final double coverageScore; // qualité détection [0, 1]
  final DateTime timestamp;

  const ExerciseFrame({
    required this.angles,
    required this.coverageScore,
    required this.timestamp,
  });

  factory ExerciseFrame.empty() => ExerciseFrame(
        angles: ExerciseAngles.empty,
        coverageScore: 0,
        timestamp: DateTime.now(),
      );

  bool get isUsable => coverageScore > 0.4;
}
