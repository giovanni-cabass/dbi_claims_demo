BeginPackage["WorkspaceFolders`"]

mainFolder::usage = "The absolute path to the project root."
outErrFiles::usage = "Directory for log and error files."
mathematicaScripts::usage = "Directory holding the .wl scripts."
mathematicaOutputs::usage = "Standard directory for .m/.tex outputs."
latexNotes::usage = "Directory holding the LaTeX notes and macros.sty."

Begin["`Private`"]

(* $InputFileName is this file's own path while Get is reading it, so the project root is just
   its grandparent directory (utils/ sits directly under the root) -- no hardcoded path. *)
mainFolder = ParentDirectory[DirectoryName[$InputFileName]];

(* Sub-folder definitions *)
outErrFiles = FileNameJoin[{mainFolder, "out_err_files"}];
mathematicaScripts = FileNameJoin[{mainFolder, "mathematica_scripts"}];
mathematicaOutputs = FileNameJoin[{mainFolder, "mathematica_outputs"}];
latexNotes = FileNameJoin[{mainFolder, "latex_notes"}];

(* Ensure the writable output folders exist (never the read-only one) *)
Scan[
    If[!DirectoryQ[#], CreateDirectory[#]] &,
    {outErrFiles, mathematicaScripts, mathematicaOutputs, latexNotes}
];

End[]
EndPackage[]
