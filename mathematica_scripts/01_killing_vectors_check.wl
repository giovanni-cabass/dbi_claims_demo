(* ::Package:: *)

(* projectRoot is this script's own location, not a hardcoded path -- utils/workspace_folders.wl
   and utils/logging_scripts.wl live alongside it. *)
projectRoot = ParentDirectory[DirectoryName[$InputFileName]];
Get[FileNameJoin[{projectRoot, "utils", "workspace_folders.wl"}]];
Get[FileNameJoin[{projectRoot, "utils", "logging_scripts.wl"}]];

Needs["WorkspaceFolders`"];
Needs["LoggingScripts`"];

(* ::Text::Regular:: *)
(* Goal: brute-force machine verification of Task 01 / latex_notes/01.starting_setup.tex.
   Independent of the two hand derivations already cross-checked in the note (the R^{1,5}
   embedding-and-project method, and the direct intrinsic-PDE-integration method), this
   script (i) derives the Christoffel symbols of the dS_5 metric G_AB = diag(-1,a^2,a^2,a^2,a^2),
   a=Exp[H t], directly from the metric via the standard formula, and checks them against the
   note's claimed closed form; (ii) plugs the note's candidate Killing vectors (spatial M^{i phi},
   i=1,2,3, and temporal M^{0 phi}) into the Killing equation nabla_(A K_B) = 0 and checks the
   residual is symbolically zero for all 15 independent components; (iii) repeats the check
   numerically at random points as an independent brute-force cross-check; (iv) checks the
   H -> 0 limit of each candidate reduces to the known flat-space Killing vectors. *)

LoggingScripts`WithStandardLogging[

    ClearAll["Global`*"];

    Module[{
        outputFolder, outputFileName, texFileName, cleanResult,
        coords, tS, x1S, x2S, x3S, phiS, HS,
        aOfT, metricG, metricGInv, christoffel, claimedChristoffel, christoffelFullMatch,
        killingResidual, spatialK, temporalK,
        spatialResidualsSym, temporalResidualsSym,
        allSpatialResidualsZero, allTemporalResidualsZero,
        randomPoints, numericSpatialMaxResidual, numericTemporalMaxResidual,
        spatialHZeroLimits, temporalHZeroLimits, hZeroLimits,
        a, b, c, i, pt,
        summary
        },

        SeedRandom[42];

        outputFolder = WorkspaceFolders`mathematicaOutputs;

        (* ----------------------------------------------------------------
           PART 0: Metric setup.
           Coordinate index map (Mathematica 1-based -> physics label):
           1 -> t (physics mu=0), 2 -> x1, 3 -> x2, 4 -> x3, 5 -> phi.
           ---------------------------------------------------------------- *)
        coords = {tS, x1S, x2S, x3S, phiS};
        aOfT = Exp[HS tS];
        metricG = DiagonalMatrix[{-1, aOfT^2, aOfT^2, aOfT^2, aOfT^2}];
        metricGInv = Inverse[metricG];

        (* ----------------------------------------------------------------
           PART 1: Christoffel symbols, brute-force from the metric.
           Gamma^a_{bc} = (1/2) g^{a sig} (d_b g_{sig c} + d_c g_{sig b} - d_sig g_{bc})
           ---------------------------------------------------------------- *)
        christoffel = Table[
            Sum[
                (1/2) metricGInv[[a, c]] * (
                    D[metricG[[c, muIdx]], coords[[nuIdx]]]
                    + D[metricG[[c, nuIdx]], coords[[muIdx]]]
                    - D[metricG[[muIdx, nuIdx]], coords[[c]]]
                ),
                {c, 1, 5}
            ],
            {a, 1, 5}, {muIdx, 1, 5}, {nuIdx, 1, 5}
        ] // FullSimplify;

        (* Claimed closed form (from the note): Gamma^0_{ab} = H a(t)^2 delta_{ab},
           Gamma^a_{0b} = H delta^a_b, for a,b spatial-incl-phi (Mathematica indices 2..5);
           all other components zero. Built explicitly and compared component-by-component
           against the full computed array -- a complete (all 125 components), not spot, check. *)
        claimedChristoffel = ConstantArray[0, {5, 5, 5}];
        Do[
            claimedChristoffel[[1, b, c]] = HS aOfT^2 KroneckerDelta[b, c],
            {b, 2, 5}, {c, 2, 5}
        ];
        Do[
            claimedChristoffel[[a, 1, c]] = HS KroneckerDelta[a, c],
            {a, 2, 5}, {c, 2, 5}
        ];
        Do[
            claimedChristoffel[[a, b, 1]] = HS KroneckerDelta[a, b],
            {a, 2, 5}, {b, 2, 5}
        ];

        christoffelFullMatch =
            (Union[Flatten[FullSimplify[christoffel - claimedChristoffel]]] === {0});

        Print["=== PART 1: Christoffel symbols vs. claimed closed form ==="];
        Print["All 125 components match the note's Gamma^0_{ab}=H a^2 delta_{ab}, Gamma^a_{0b}=H delta^a_b (else 0): ",
            christoffelFullMatch];

        (* ----------------------------------------------------------------
           PART 2: Killing-equation residual, brute force.
           Residual_{AB} = d_A K_B + d_B K_A - 2 Gamma^C_{AB} K_C,  K_B = g_{BC} K^C.
           A Killing vector requires Residual_{AB} = 0 for all A,B.
           ---------------------------------------------------------------- *)
        killingResidual[KUpper_List] := Module[{KLower},
            KLower = metricG . KUpper;
            Table[
                D[KLower[[b]], coords[[a]]] + D[KLower[[a]], coords[[b]]]
                - 2 Sum[christoffel[[c, a, b]] KLower[[c]], {c, 1, 5}],
                {a, 1, 5}, {b, 1, 5}
            ]
        ];

        (* ----------------------------------------------------------------
           PART 3: Candidate Killing vectors, verbatim from 01.starting_setup.tex.
           ---------------------------------------------------------------- *)
        spatialK[i_] := Module[{K},
            K = ConstantArray[0, 5];
            K[[i + 1]] = phiS;
            K[[5]] = -coords[[i + 1]];
            K
        ];

        temporalK = {
            phiS,
            -HS phiS x1S,
            -HS phiS x2S,
            -HS phiS x3S,
            (Exp[-HS tS] Sinh[HS tS])/HS + (HS/2) (x1S^2 + x2S^2 + x3S^2 - phiS^2)
        };

        (* ----------------------------------------------------------------
           PART 4: Symbolic verification of the Killing equation.
           ---------------------------------------------------------------- *)
        spatialResidualsSym = Table[FullSimplify[killingResidual[spatialK[i]]], {i, 1, 3}];
        allSpatialResidualsZero = Table[
            Union[Flatten[spatialResidualsSym[[i]]]] === {0},
            {i, 1, 3}
        ];

        temporalResidualsSym = FullSimplify[killingResidual[temporalK]];
        allTemporalResidualsZero = (Union[Flatten[temporalResidualsSym]] === {0});

        Print[""];
        Print["=== PART 2-4: Killing equation residual (symbolic) ==="];
        Print["Spatial M^{i phi}, i=1,2,3 -- residual identically zero: ", allSpatialResidualsZero];
        Print["Temporal M^{0 phi} -- residual identically zero: ", allTemporalResidualsZero];

        (* ----------------------------------------------------------------
           PART 5: Independent numerical brute-force spot-check at random points.
           ---------------------------------------------------------------- *)
        randomPoints = Table[
            {
                tS -> RandomReal[{-2, 2}], x1S -> RandomReal[{-2, 2}],
                x2S -> RandomReal[{-2, 2}], x3S -> RandomReal[{-2, 2}],
                phiS -> RandomReal[{-2, 2}], HS -> RandomReal[{0.1, 2}]
            },
            {5}
        ];

        numericSpatialMaxResidual = Table[
            Max[Table[Max[Abs[Flatten[killingResidual[spatialK[i]] /. pt]]], {pt, randomPoints}]],
            {i, 1, 3}
        ];
        numericTemporalMaxResidual =
            Max[Table[Max[Abs[Flatten[killingResidual[temporalK] /. pt]]], {pt, randomPoints}]];

        Print[""];
        Print["=== PART 5: Numeric spot-check (5 random points, SeedRandom[42]) ==="];
        Print["Spatial i=1,2,3, max |residual|: ", numericSpatialMaxResidual];
        Print["Temporal, max |residual|: ", numericTemporalMaxResidual];

        (* ----------------------------------------------------------------
           PART 6: H -> 0 limit check against the known flat-space Killing vectors.
           Expected: Spatial i: K^0=0, K^i=phi, K^{j!=i}=0, K^phi=-x^i (H-independent).
                     Temporal:  K^0=phi, K^i=0, K^phi=t.
           ---------------------------------------------------------------- *)
        spatialHZeroLimits = Table[Limit[spatialK[i], HS -> 0], {i, 1, 3}];
        temporalHZeroLimits = Limit[temporalK, HS -> 0];

        hZeroLimits = <|
            "Spatial i=1 -> {0,phi,0,0,-x1}" -> (spatialHZeroLimits[[1]] === {0, phiS, 0, 0, -x1S}),
            "Spatial i=2 -> {0,0,phi,0,-x2}" -> (spatialHZeroLimits[[2]] === {0, 0, phiS, 0, -x2S}),
            "Spatial i=3 -> {0,0,0,phi,-x3}" -> (spatialHZeroLimits[[3]] === {0, 0, 0, phiS, -x3S}),
            "Temporal -> {phi,0,0,0,t}" -> (temporalHZeroLimits === {phiS, 0, 0, 0, tS})
        |>;

        Print[""];
        Print["=== PART 6: H -> 0 limit checks ==="];
        Print[hZeroLimits];

        (* ----------------------------------------------------------------
           SAVE
           ---------------------------------------------------------------- *)
        summary = <|
            "ChristoffelFullMatch" -> christoffelFullMatch,
            "SpatialKillingResidualsAllZero_i123" -> allSpatialResidualsZero,
            "TemporalKillingResidualsAllZero" -> allTemporalResidualsZero,
            "NumericSpotCheckMaxResidual_Spatial_i123" -> numericSpatialMaxResidual,
            "NumericSpotCheckMaxResidual_Temporal" -> numericTemporalMaxResidual,
            "HZeroLimitChecks" -> hZeroLimits
        |>;

        outputFileName = FileNameJoin[{outputFolder, "01_killing_vectors_check.m"}];
        Put[summary, outputFileName];

        cleanResult = summary /. HoldPattern[sym_Symbol] :>
            ToExpression[StringReplace[ToString[sym], RegularExpression["\\$\\d+$"] -> ""]];
        texFileName = FileNameJoin[{outputFolder, "01_killing_vectors_check.tex"}];
        Export[texFileName, TeXForm[cleanResult], "Text"];

        Print[""];
        Print["Saved to: ", outputFileName];
        Print["TeX snippet saved to: ", texFileName];
    ];

];
