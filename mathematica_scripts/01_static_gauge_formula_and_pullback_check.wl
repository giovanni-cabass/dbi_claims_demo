(* ::Package:: *)

(* projectRoot is this script's own location, not a hardcoded path -- utils/workspace_folders.wl
   and utils/logging_scripts.wl live alongside it. *)
projectRoot = ParentDirectory[DirectoryName[$InputFileName]];
Get[FileNameJoin[{projectRoot, "utils", "workspace_folders.wl"}]];
Get[FileNameJoin[{projectRoot, "utils", "logging_scripts.wl"}]];

Needs["WorkspaceFolders`"];
Needs["LoggingScripts`"];

(* ::Text::Regular:: *)
(* Goal: machine-verify the three pieces of latex_notes/01.starting_setup.tex that the sibling
   script mathematica_scripts/01_killing_vectors_check.wl does NOT cover (that script already
   cleanly verifies the three Killing vectors themselves -- Christoffels, Killing equation,
   H->0 limit -- treated here as already-established, correct input data, never re-derived).

   Part 1: the general static-gauge formula eq:static-gauge-formula,
       delta phi = K^phi|_{X=(x,phi)} - K^mu|_{X=(x,phi)} partial_mu phi ,
   derived structurally for FULLY GENERIC abstract K^mu(x,phi), K^phi(x,phi), phi(x^mu) -- not
   specialized to any particular generator. Ambient shift delta X^A = eps K^A; worldvolume label
   re-fixed to O(eps) by inverting tildex^mu = x^mu + eps K^mu; O(eps) coefficient of
   tildephi(tildex)-phi(tildex) extracted via Series and compared to the general formula.
   Confirmed two independent ways: (i) fully symbolic, with phi and all K^A left as abstract
   (undefined) functions -- Mathematica's Series/D produce the generic chain-rule structure via
   Derivative[...][phiF][...], and FullSimplify closes the residual to exactly 0; (ii) a fully
   numeric cross-check with concrete random-coefficient polynomial stand-ins for phi and the
   four K^A, where the O(eps) coefficient is extracted by an INDEPENDENT finite-difference route
   that never uses the approximate O(eps) inverse map: FindRoot inverts the exact finite-eps
   forward map at a sequence of shrinking eps, and the finite difference is checked to converge
   linearly (residual ~ eps) onto the analytic formula's value.

   Part 2: substitutes the three already-established Killing vectors (spatial M^{1 phi}, temporal
   M^{0 phi}, flat M^{mu 5}) into the Part-1 general formula and checks the result against the
   note's eq:delta-phi-spatial, eq:delta-phi-temporal, eq:flat-dbi-boost.

   Part 3: the induced-metric pullback eq:induced-metric, tilde g_{mu nu} = G_{AB} dX^A/dx^mu
   dX^B/dx^nu, checked against g^{dS}_{mu nu} + a(t)^2 partial_mu phi partial_nu phi for fully
   generic phi(x^mu) and generic a(t) (not restricted to a=e^{H t}) -- symbolically and at a
   numeric spot-check.

   Convention assumed throughout (matching 01.starting_setup.tex exactly): metric signature
   diag(-1,+1,+1,+1[,+1]); eq:static-gauge-formula sign delta phi = K^phi - K^mu partial_mu phi
   (NOT the b -> -b convention of 2404.01894v2, noted explicitly in the note's Sec. 4.3/5.4).
   Mathematica index 1 -> physics t (mu=0), indices 2,3,4 -> x1,x2,x3, index 5 -> phi, exactly as
   in 01_killing_vectors_check.wl. *)

LoggingScripts`WithStandardLogging[

    ClearAll["Global`*"];

    Module[{
        outputFolder, outputFileName, texFileName, cleanResult,
        tS, x1S, x2S, x3S, HS, b0S, b1S, b2S, b3S,
        coordsOld, phiF, K0F, K1F, K2F, K3F, KphiF, epsS,
        kUpperFuncAbstract, forwardMapAbstract, candidateInverseAbstract,
        checkInverseSeries, checkInverseResidual,
        tildePhiAtOldFn, tildePhiAtNewSeries, tildePhiAtNewNormal,
        zerothOrderCheck, deltaPhiExtracted, gradPhiNew, generalFormulaAbstract,
        part1SymbolicResidual, part1SymbolicPass,
        coefsPhi, coefsK0, coefsK1, coefsK2, coefsK3, coefsKphi,
        phiFNum, K0FNum, K1FNum, K2FNum, K3FNum, KphiFNum,
        kUpperFuncNum, forwardMapNum, Yval, deltaPhiAnalyticNum,
        epsList, numericFiniteDiffResiduals, aVar0, aVar1, aVar2, aVar3, solFindRoot, xOldSolNum,
        ambientPhiNewNum, finiteDiffNum, part1NumericPass, part1NumericRatiosOK,
        gradPhi, staticGaugeFormula,
        kUpperSpatial, kPhiSpatial, deltaPhiSpatial, expectedSpatial, residualSpatial,
        kUpperTemporal, kPhiTemporal, deltaPhiTemporal, expectedTemporal, residualTemporal,
        bUpper, etaLower, bLower, kUpperFlat, kPhiFlat, deltaPhiFlat, expectedFlat, residualFlat,
        part2Pass,
        aFunc, aT, gAmbient, jac, tildeGSymbolic, gDS, claimedTildeG, part3SymbolicResidual,
        part3SymbolicPass,
        aFuncNumFn, phiFNum3, tildeGNum, claimedTildeGNum, part3NumericResidual, part3NumericPass,
        randPointPart3,
        summary
        },

        SeedRandom[42];

        outputFolder = WorkspaceFolders`mathematicaOutputs;

        (* ============================================================
           PART 1: General static-gauge formula, fully generic K^A, phi.
           ============================================================ *)

        (* ---- 1a. Symbolic derivation with abstract (undefined) functions ---- *)
        coordsOld = {tS, x1S, x2S, x3S};

        (* kUpperFuncAbstract[args]: the four K^mu components, each K^mu(x, phi(x)),
           evaluated with phi restricted to the brane (phi -> phiF[args]). *)
        kUpperFuncAbstract[args_List] := {
            K0F[Sequence @@ args, phiF[Sequence @@ args]],
            K1F[Sequence @@ args, phiF[Sequence @@ args]],
            K2F[Sequence @@ args, phiF[Sequence @@ args]],
            K3F[Sequence @@ args, phiF[Sequence @@ args]]
        };

        (* Ambient shift: tildex^mu(x) = x^mu + eps K^mu(x,phi(x)) -- the forward map on the
           worldvolume label induced by delta X^mu = eps K^mu. *)
        forwardMapAbstract[argsOld_List] := argsOld + epsS * kUpperFuncAbstract[argsOld];

        (* Candidate O(eps) inverse: x^mu(tildex) = tildex^mu - eps K^mu(tildex,phi(tildex)).
           Verified below (not assumed) by composing forward and inverse to O(eps). *)
        candidateInverseAbstract[argsNew_List] := argsNew - epsS * kUpperFuncAbstract[argsNew];

        checkInverseSeries =
            Series[forwardMapAbstract[candidateInverseAbstract[coordsOld]], {epsS, 0, 1}] // Normal;
        checkInverseResidual = FullSimplify[checkInverseSeries - coordsOld];

        Print["=== PART 1a: candidate O(eps) inverse composes to the identity, residual: ==="];
        Print[checkInverseResidual];

        (* tildephi(x), expressed on the OLD label x: the shifted ambient phi-coordinate value. *)
        tildePhiAtOldFn[argsOld_List] :=
            phiF[Sequence @@ argsOld] + epsS * KphiF[Sequence @@ argsOld, phiF[Sequence @@ argsOld]];

        (* Re-express on the NEW label (tildex, i.e. coordsOld again, reused as the free symbol
           after relabeling) by composing with the inverse map, then Series-expand to O(eps). *)
        tildePhiAtNewSeries = Series[tildePhiAtOldFn[candidateInverseAbstract[coordsOld]], {epsS, 0, 1}];
        tildePhiAtNewNormal = Normal[tildePhiAtNewSeries];

        zerothOrderCheck = FullSimplify[(tildePhiAtNewNormal /. epsS -> 0) - phiF[Sequence @@ coordsOld]];
        deltaPhiExtracted = Coefficient[tildePhiAtNewNormal, epsS, 1];

        gradPhiNew = D[phiF[Sequence @@ coordsOld], #] & /@ coordsOld;
        generalFormulaAbstract = KphiF[Sequence @@ coordsOld, phiF[Sequence @@ coordsOld]]
            - kUpperFuncAbstract[coordsOld] . gradPhiNew;

        part1SymbolicResidual = FullSimplify[deltaPhiExtracted - generalFormulaAbstract];
        part1SymbolicPass = (part1SymbolicResidual === 0) && (zerothOrderCheck === 0);

        Print[""];
        Print["=== PART 1b: symbolic O(eps) coefficient of tildephi(tildex)-phi(tildex) ==="];
        Print["Extracted: ", deltaPhiExtracted];
        Print["General formula K^phi - K^mu partial_mu phi: ", generalFormulaAbstract];
        Print["Zeroth-order check (expect 0): ", zerothOrderCheck];
        Print["Residual (expect 0): ", part1SymbolicResidual];
        Print["PART 1 symbolic PASS: ", part1SymbolicPass];

        (* ---- 1c. Independent numeric cross-check: concrete random functions, exact finite-eps
                   inversion via FindRoot (never uses the O(eps) approximate inverse above),
                   finite-difference extraction of the O(eps) coefficient, checked to converge
                   linearly onto the analytic formula as eps -> 0. ---- *)
        coefsPhi = RandomReal[{-1, 1}, 5];
        coefsK0 = RandomReal[{-1, 1}, 6];
        coefsK1 = RandomReal[{-1, 1}, 6];
        coefsK2 = RandomReal[{-1, 1}, 6];
        coefsK3 = RandomReal[{-1, 1}, 6];
        coefsKphi = RandomReal[{-1, 1}, 6];

        phiFNum[t_, x1_, x2_, x3_] :=
            coefsPhi[[1]] + coefsPhi[[2]] t + coefsPhi[[3]] x1 + coefsPhi[[4]] x2 + coefsPhi[[5]] x3;
        K0FNum[t_, x1_, x2_, x3_, p_] :=
            coefsK0[[1]] + coefsK0[[2]] t + coefsK0[[3]] x1 + coefsK0[[4]] x2 + coefsK0[[5]] x3 + coefsK0[[6]] p;
        K1FNum[t_, x1_, x2_, x3_, p_] :=
            coefsK1[[1]] + coefsK1[[2]] t + coefsK1[[3]] x1 + coefsK1[[4]] x2 + coefsK1[[5]] x3 + coefsK1[[6]] p;
        K2FNum[t_, x1_, x2_, x3_, p_] :=
            coefsK2[[1]] + coefsK2[[2]] t + coefsK2[[3]] x1 + coefsK2[[4]] x2 + coefsK2[[5]] x3 + coefsK2[[6]] p;
        K3FNum[t_, x1_, x2_, x3_, p_] :=
            coefsK3[[1]] + coefsK3[[2]] t + coefsK3[[3]] x1 + coefsK3[[4]] x2 + coefsK3[[5]] x3 + coefsK3[[6]] p;
        KphiFNum[t_, x1_, x2_, x3_, p_] :=
            coefsKphi[[1]] + coefsKphi[[2]] t + coefsKphi[[3]] x1 + coefsKphi[[4]] x2 + coefsKphi[[5]] x3 + coefsKphi[[6]] p;

        kUpperFuncNum[args_List] := {
            K0FNum[Sequence @@ args, phiFNum[Sequence @@ args]],
            K1FNum[Sequence @@ args, phiFNum[Sequence @@ args]],
            K2FNum[Sequence @@ args, phiFNum[Sequence @@ args]],
            K3FNum[Sequence @@ args, phiFNum[Sequence @@ args]]
        };
        forwardMapNum[argsOld_List, epsVal_] := argsOld + epsVal * kUpperFuncNum[argsOld];

        Yval = RandomReal[{-2, 2}, 4];

        deltaPhiAnalyticNum = KphiFNum[Sequence @@ Yval, phiFNum[Sequence @@ Yval]]
            - kUpperFuncNum[Yval] . {coefsPhi[[2]], coefsPhi[[3]], coefsPhi[[4]], coefsPhi[[5]]};

        epsList = {10^-3, 10^-4, 10^-5, 10^-6};
        numericFiniteDiffResiduals = Table[
            solFindRoot = FindRoot[
                forwardMapNum[{aVar0, aVar1, aVar2, aVar3}, epsVal] == Yval,
                {{aVar0, Yval[[1]]}, {aVar1, Yval[[2]]}, {aVar2, Yval[[3]]}, {aVar3, Yval[[4]]}}
            ];
            xOldSolNum = {aVar0, aVar1, aVar2, aVar3} /. solFindRoot;
            ambientPhiNewNum = phiFNum[Sequence @@ xOldSolNum]
                + epsVal * KphiFNum[Sequence @@ xOldSolNum, phiFNum[Sequence @@ xOldSolNum]];
            finiteDiffNum = (ambientPhiNewNum - phiFNum[Sequence @@ Yval]) / epsVal;
            Abs[finiteDiffNum - deltaPhiAnalyticNum],
            {epsVal, epsList}
        ];

        (* Expect linear convergence: residual ~ eps, so each successive residual ~ 1/10 of the
           previous one (epsList shrinks by 10x each step). Checked loosely (ratio in [5,20]). *)
        part1NumericRatiosOK = AllTrue[
            Table[numericFiniteDiffResiduals[[i]] / numericFiniteDiffResiduals[[i + 1]], {i, 1, 3}],
            (5 < # < 20) &
        ];
        part1NumericPass = (Last[numericFiniteDiffResiduals] < 10^-4) && part1NumericRatiosOK;

        Print[""];
        Print["=== PART 1c: independent numeric finite-difference cross-check ==="];
        Print["eps values: ", epsList];
        Print["|finite-diff - analytic| at each eps: ", numericFiniteDiffResiduals];
        Print["Linear-convergence ratios (expect ~10 each): ",
            Table[numericFiniteDiffResiduals[[i]] / numericFiniteDiffResiduals[[i + 1]], {i, 1, 3}]];
        Print["PART 1 numeric PASS: ", part1NumericPass];

        (* ============================================================
           PART 2: substitute the three already-established Killing vectors
           into the Part-1 general formula; compare to the note's results.
           ============================================================ *)

        gradPhi = D[phiF[Sequence @@ coordsOld], #] & /@ coordsOld;
        staticGaugeFormula[kUpper_List, kPhi_] := kPhi - kUpper . gradPhi;

        (* -- Spatial M^{1 phi} (i=1 WLOG), eq:spatial-killing -> eq:delta-phi-spatial -- *)
        kUpperSpatial = {0, phiF[Sequence @@ coordsOld], 0, 0};
        kPhiSpatial = -x1S;
        deltaPhiSpatial = staticGaugeFormula[kUpperSpatial, kPhiSpatial] // Simplify;
        expectedSpatial = -x1S - phiF[Sequence @@ coordsOld] * D[phiF[Sequence @@ coordsOld], x1S];
        residualSpatial = FullSimplify[deltaPhiSpatial - expectedSpatial];

        (* -- Temporal M^{0 phi}, eq:temporal-killing -> eq:delta-phi-temporal -- *)
        kUpperTemporal = {
            phiF[Sequence @@ coordsOld],
            -HS * phiF[Sequence @@ coordsOld] * x1S,
            -HS * phiF[Sequence @@ coordsOld] * x2S,
            -HS * phiF[Sequence @@ coordsOld] * x3S
        };
        kPhiTemporal = (Exp[-HS tS] Sinh[HS tS]) / HS
            + (HS / 2) (x1S^2 + x2S^2 + x3S^2 - phiF[Sequence @@ coordsOld]^2);
        deltaPhiTemporal = staticGaugeFormula[kUpperTemporal, kPhiTemporal] // Simplify;
        expectedTemporal = (Exp[-HS tS] Sinh[HS tS]) / HS
            + (HS / 2) (x1S^2 + x2S^2 + x3S^2 - phiF[Sequence @@ coordsOld]^2)
            - phiF[Sequence @@ coordsOld] * D[phiF[Sequence @@ coordsOld], tS]
            + HS * phiF[Sequence @@ coordsOld] * (
                x1S * D[phiF[Sequence @@ coordsOld], x1S]
                + x2S * D[phiF[Sequence @@ coordsOld], x2S]
                + x3S * D[phiF[Sequence @@ coordsOld], x3S]
            );
        residualTemporal = FullSimplify[deltaPhiTemporal - expectedTemporal];

        (* -- Flat M^{mu 5}, general b^mu, eq:flat-dbi-boost -- *)
        bUpper = {b0S, b1S, b2S, b3S};
        etaLower = {-1, 1, 1, 1};
        bLower = etaLower * bUpper;
        kUpperFlat = bUpper * phiF[Sequence @@ coordsOld];
        kPhiFlat = -bLower . coordsOld;
        deltaPhiFlat = staticGaugeFormula[kUpperFlat, kPhiFlat] // Simplify;
        expectedFlat = -(bUpper . gradPhi) * phiF[Sequence @@ coordsOld] - bLower . coordsOld;
        residualFlat = FullSimplify[deltaPhiFlat - expectedFlat];

        part2Pass = (residualSpatial === 0) && (residualTemporal === 0) && (residualFlat === 0);

        Print[""];
        Print["=== PART 2: substitute the three Killing vectors into the general formula ==="];
        Print["Spatial M^{1 phi}: delta phi = ", deltaPhiSpatial];
        Print["  residual vs. note's eq:delta-phi-spatial (expect 0): ", residualSpatial];
        Print["Temporal M^{0 phi}: delta phi = ", deltaPhiTemporal];
        Print["  residual vs. note's eq:delta-phi-temporal (expect 0): ", residualTemporal];
        Print["Flat M^{mu 5} (general b^mu): delta phi = ", deltaPhiFlat];
        Print["  residual vs. note's eq:flat-dbi-boost (expect 0): ", residualFlat];
        Print["PART 2 PASS: ", part2Pass];

        (* ============================================================
           PART 3: induced-metric pullback, eq:induced-metric.
           Fully generic phi(x^mu) and generic a(t) (not fixed to e^{H t}).
           ============================================================ *)

        aT = aFunc[tS];
        gAmbient = DiagonalMatrix[{-1, aT^2, aT^2, aT^2, aT^2}];

        (* Jacobian dX^A/dx^mu = delta^A_mu + delta^A_phi partial_mu phi.
           Row A runs 1..5 (t,x1,x2,x3,phi); column mu runs 1..4 (t,x1,x2,x3). *)
        jac = Table[
            If[aIdxLocal <= 4, KroneckerDelta[aIdxLocal, muIdxLocal], gradPhi[[muIdxLocal]]],
            {aIdxLocal, 1, 5}, {muIdxLocal, 1, 4}
        ];

        tildeGSymbolic = Transpose[jac] . gAmbient . jac // Simplify;

        gDS = DiagonalMatrix[{-1, aT^2, aT^2, aT^2}];
        claimedTildeG = gDS + aT^2 * Outer[Times, gradPhi, gradPhi];

        part3SymbolicResidual = FullSimplify[tildeGSymbolic - claimedTildeG];
        part3SymbolicPass = (Union[Flatten[part3SymbolicResidual]] === {0});

        Print[""];
        Print["=== PART 3a: induced metric pullback, symbolic (generic phi, generic a(t)) ==="];
        Print["tilde g_{mu nu}: ", tildeGSymbolic];
        Print["Residual vs. g^dS_{mu nu} + a^2 partial_mu phi partial_nu phi (expect all 0): ",
            part3SymbolicResidual];
        Print["PART 3 symbolic PASS: ", part3SymbolicPass];

        (* ---- 3b. Numeric spot-check with a concrete a(t) and phi(x), random point ---- *)
        aFuncNumFn[t_] := 1 + 0.3 t + 0.1 t^2;
        phiFNum3[t_, x1_, x2_, x3_] := 0.4 t + 0.2 x1 - 0.3 x2*t + 0.15 x3^2;

        randPointPart3 = {tS -> RandomReal[{-1, 1}], x1S -> RandomReal[{-1, 1}],
            x2S -> RandomReal[{-1, 1}], x3S -> RandomReal[{-1, 1}]};

        tildeGNum = N[(tildeGSymbolic /. {aFunc -> aFuncNumFn, phiF -> phiFNum3}) /. randPointPart3];
        claimedTildeGNum = N[(claimedTildeG /. {aFunc -> aFuncNumFn, phiF -> phiFNum3}) /. randPointPart3];
        part3NumericResidual = Max[Abs[Flatten[tildeGNum - claimedTildeGNum]]];
        part3NumericPass = part3NumericResidual < 10^-10;

        Print[""];
        Print["=== PART 3b: numeric spot-check (concrete a(t), phi(x), random point) ==="];
        Print["Max |residual|: ", part3NumericResidual];
        Print["PART 3 numeric PASS: ", part3NumericPass];

        (* ----------------------------------------------------------------
           SAVE
           ---------------------------------------------------------------- *)
        summary = <|
            "Part1_GeneralFormula" -> generalFormulaAbstract,
            "Part1_SymbolicResidual" -> part1SymbolicResidual,
            "Part1_SymbolicPass" -> part1SymbolicPass,
            "Part1_NumericFiniteDiffResiduals" -> numericFiniteDiffResiduals,
            "Part1_NumericPass" -> part1NumericPass,
            "Part2_DeltaPhiSpatial" -> deltaPhiSpatial,
            "Part2_ResidualSpatial" -> residualSpatial,
            "Part2_DeltaPhiTemporal" -> deltaPhiTemporal,
            "Part2_ResidualTemporal" -> residualTemporal,
            "Part2_DeltaPhiFlat" -> deltaPhiFlat,
            "Part2_ResidualFlat" -> residualFlat,
            "Part2_Pass" -> part2Pass,
            "Part3_InducedMetric" -> tildeGSymbolic,
            "Part3_SymbolicResidual" -> part3SymbolicResidual,
            "Part3_SymbolicPass" -> part3SymbolicPass,
            "Part3_NumericResidual" -> part3NumericResidual,
            "Part3_NumericPass" -> part3NumericPass
        |>;

        outputFileName = FileNameJoin[{outputFolder, "01_static_gauge_formula_and_pullback_check.m"}];
        Put[summary, outputFileName];

        cleanResult = summary /. HoldPattern[sym_Symbol] :>
            ToExpression[StringReplace[ToString[sym], RegularExpression["\\$\\d+$"] -> ""]];
        texFileName = FileNameJoin[{outputFolder, "01_static_gauge_formula_and_pullback_check.tex"}];
        Export[texFileName, TeXForm[cleanResult], "Text"];

        Print[""];
        Print["Saved to: ", outputFileName];
        Print["TeX snippet saved to: ", texFileName];
    ];

];
