BeginPackage["LoggingScripts`"]
Needs["WorkspaceFolders`"]

WithStandardLogging::usage = "WithStandardLogging[expr] executes expr with stdout/stderr teed to files."

Begin["`Private`"]

WithStandardLogging[code_] := Module[{
    scriptPath, scriptName, timestamp, tz, 
    outFileName, errFileName, outPath, errPath,
    outFile, errFile, result
},
    scriptPath = $InputFileName;
    scriptName = If[scriptPath === "", "interactive", FileBaseName[scriptPath]];
    
    timestamp = DateString[{"Year", "Month", "Day", "_", "Hour", "Minute", "Second"}];
    tz = If[Length[$TimeZoneName] > 0, First[StringSplit[$TimeZoneName]], "UTC"];

    outFileName = scriptName <> "_output_" <> timestamp <> "_" <> tz <> ".txt";
    errFileName = scriptName <> "_errors_" <> timestamp <> "_" <> tz <> ".txt";
    
    outPath = FileNameJoin[{WorkspaceFolders`outErrFiles, outFileName}];
    errPath = FileNameJoin[{WorkspaceFolders`outErrFiles, errFileName}];

    outFile = OpenWrite[outPath, CharacterEncoding -> "UTF8"];
    errFile = OpenWrite[errPath, CharacterEncoding -> "UTF8"];

    Internal`WithLocalSettings[
        AppendTo[$Output, outFile];
        AppendTo[$Messages, errFile]; 
        (*SetOptions[outFile, FormatType -> OutputForm];*)
        (*SetOptions[errFile, FormatType -> OutputForm];*)
        SetOptions[$Output, CharacterEncoding -> "UTF-8"];
        SetOptions[$Messages, CharacterEncoding -> "UTF-8"];
        Print["🚀 Script: ", scriptName, ".wl"];
        Print["📅 Started: ", DateString[{"DayName", " ", "MonthName", " ", "Day", ", ", "Year", " ", "Hour", ":", "Minute", ":", "Second"}]];
        ,
        result = code;
        ,
        Print["🏁 Execution finished."];
        $Output = DeleteCases[$Output, outFile];
        $Messages = DeleteCases[$Messages, errFile];
        Close[outFile];
        Close[errFile];
        Print["✅ Logs saved to: ", WorkspaceFolders`outErrFiles];
    ];
    result
]

SetAttributes[WithStandardLogging, HoldFirst]

End[]
EndPackage[]
