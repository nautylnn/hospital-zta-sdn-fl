%% ============================================================================
%% hcmut-thesis.cls - Graduation Thesis Class (HCMUT - VNU-HCM, English Program)
%% Based on HCMUT OISP / Faculty of Computer Science and Engineering format
%% ============================================================================
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{hcmut-thesis}[2026/11/25 HCMUT Graduation Thesis Class (English)]

\LoadClass[12pt,a4paper,oneside]{report}

% --- Encoding, Fonts, and Geometry ---
% vntex + T5 are kept so Vietnamese proper names and the bilingual Tóm tắt
% compile natively under pdflatex without Unicode font issues.
\RequirePackage[utf8]{vntex}
\RequirePackage[utf8]{inputenc}
\RequirePackage[T5]{fontenc}
\RequirePackage{mathptmx}
\RequirePackage{geometry}
\geometry{
  a4paper,
  left=3.5cm,
  right=2.0cm,
  top=2.5cm,
  bottom=2.5cm,
  headheight=15pt
}

% --- Core Packages ---
\RequirePackage{graphicx}
\RequirePackage{amsmath,amssymb}
\RequirePackage{booktabs,array,longtable,tabularx,multirow}
\RequirePackage{setspace}
\RequirePackage{titlesec}
\RequirePackage{fancyhdr}
\RequirePackage{enumitem}
\RequirePackage{xcolor}
\RequirePackage{tikz}
\usetikzlibrary{calc}
\RequirePackage[noadjust]{cite}
\RequirePackage[hidelinks,bookmarks=true,unicode=true,plainpages=false,pdfpagelabels=true]{hyperref}

% --- Override vntex labels with English Academic Headings ---
\AtBeginDocument{%
  \renewcommand{\contentsname}{Table of Contents}%
  \renewcommand{\listfigurename}{List of Figures}%
  \renewcommand{\listtablename}{List of Tables}%
  \renewcommand{\bibname}{References}%
  \renewcommand{\figurename}{Figure}%
  \renewcommand{\tablename}{Table}%
  \renewcommand{\chaptername}{CHAPTER}%
}

% --- Spacing and Paragraph Formatting ---
\onehalfspacing
\setlength{\parindent}{1.0cm}
\setlength{\parskip}{6pt plus 2pt minus 1pt}

% --- Chapter & Section Formatting ---
\titleformat{\chapter}[display]
  {\normalfont\bfseries\centering\fontsize{16}{20}\selectfont}
  {CHAPTER \thechapter}
  {8pt}
  {\fontsize{16}{20}\selectfont}
\titlespacing*{\chapter}{0pt}{-10pt}{20pt}

\titleformat{\section}
  {\normalfont\bfseries\fontsize{14}{17}\selectfont}
  {\thesection}
  {0.8em}
  {}
\titlespacing*{\section}{0pt}{14pt}{6pt}

\titleformat{\subsection}
  {\normalfont\bfseries\fontsize{13}{16}\selectfont}
  {\thesubsection}
  {0.8em}
  {}
\titlespacing*{\subsection}{0pt}{10pt}{4pt}

\titleformat{\subsubsection}
  {\normalfont\bfseries\itshape\fontsize{12}{15}\selectfont}
  {\thesubsubsection}
  {0.8em}
  {}
\titlespacing*{\subsubsection}{0pt}{8pt}{3pt}

% --- Header & Footer Styles ---
\fancypagestyle{thesis}{%
  \fancyhf{}%
  \fancyhead[L]{\small\itshape Graduation Thesis -- Faculty of Computer Science and Engineering}%
  \fancyhead[R]{\small\itshape HCMUT -- VNU-HCM}%
  \fancyfoot[C]{\thepage}%
  \renewcommand{\headrulewidth}{0.4pt}%
  \renewcommand{\footrulewidth}{0pt}%
}
\fancypagestyle{plain}{%
  \fancyhf{}%
  \fancyfoot[C]{\thepage}%
  \renewcommand{\headrulewidth}{0pt}%
}
\pagestyle{thesis}

% --- Metadata Macros ---
\newcommand{\@upperuni}{VIETNAM NATIONAL UNIVERSITY HO CHI MINH CITY}
\newcommand{\@university}{HO CHI MINH CITY UNIVERSITY OF TECHNOLOGY}
\newcommand{\@faculty}{FACULTY OF COMPUTER SCIENCE AND ENGINEERING}
\newcommand{\@thesistype}{GRADUATION THESIS}
\newcommand{\@major}{MAJOR: COMPUTER ENGINEERING}
\newcommand{\@thesistitle}{Thesis Title}
\newcommand{\@advisor}{Advisor Name}
\newcommand{\@students}{Student List}
\newcommand{\@subcoverstudents}{Student List}
\newcommand{\@place}{HO CHI MINH CITY}
\newcommand{\@dateyear}{NOVEMBER 2026}

\newcommand{\upperuni}[1]{\renewcommand{\@upperuni}{#1}}
\newcommand{\university}[1]{\renewcommand{\@university}{#1}}
\newcommand{\faculty}[1]{\renewcommand{\@faculty}{#1}}
\newcommand{\thesistype}[1]{\renewcommand{\@thesistype}{#1}}
\newcommand{\major}[1]{\renewcommand{\@major}{#1}}
\newcommand{\thesistitle}[1]{\renewcommand{\@thesistitle}{#1}}
\newcommand{\advisor}[1]{\renewcommand{\@advisor}{#1}}
\newcommand{\students}[1]{\renewcommand{\@students}{#1}}
\newcommand{\subcoverstudents}[1]{\renewcommand{\@subcoverstudents}{#1}}
\newcommand{\place}[1]{\renewcommand{\@place}{#1}}
\newcommand{\dateyear}[1]{\renewcommand{\@dateyear}{#1}}

% --- Front Matter Chapter Helper (unnumbered, added to ToC) ---
\newcommand{\frontchapter}[1]{%
  \clearpage
  \chapter*{#1}%
  \addcontentsline{toc}{chapter}{#1}%
}

% --- Cover Border Drawing Helper ---
\newcommand{\@drawcoverframe}{%
  \begin{tikzpicture}[remember picture, overlay]
    \draw[line width=2.2pt]
      ($(current page.north west) + (2.0cm,-1.6cm)$)
      rectangle
      ($(current page.south east) + (-1.6cm,1.6cm)$);
    \draw[line width=0.8pt]
      ($(current page.north west) + (2.15cm,-1.75cm)$)
      rectangle
      ($(current page.south east) + (-1.75cm,1.75cm)$);
  \end{tikzpicture}%
}

% --- Main Cover Page (Hard Cover) ---
\newcommand{\makecoverpage}{%
  \begin{titlepage}
    \@drawcoverframe
    \centering
    \vspace*{0.2cm}
    {\fontsize{12}{15}\selectfont\bfseries \@upperuni \par}
    {\fontsize{13}{16}\selectfont\bfseries \@university \par}
    {\fontsize{12}{15}\selectfont\bfseries \@faculty \par}

    \vspace{0.8cm}
    \includegraphics[width=2.8cm]{graphics/hcmut.png}

    \vspace{0.8cm}
    {\fontsize{16}{20}\selectfont\bfseries \@thesistype \par}
    \vspace{0.25cm}
    {\fontsize{12}{15}\selectfont\bfseries \@major \par}

    \vspace{1.2cm}
    \begin{minipage}{0.88\textwidth}
      \centering
      \setstretch{1.35}
      {\fontsize{15}{21}\selectfont\bfseries \@thesistitle \par}
    \end{minipage}

    \vfill
    \begin{flushleft}
      \hspace{2.2cm}
      \begin{tabular}{@{}l l@{}}
        \textbf{Advisor:}  & \@advisor \\[6pt]
        \textbf{Students:} & \begin{tabular}[t]{@{}l@{}} \@students \end{tabular}
      \end{tabular}
    \end{flushleft}

    \vspace{1.4cm}
    {\fontsize{12}{15}\selectfont\bfseries \@place, \@dateyear \par}
    \vspace*{0.2cm}
  \end{titlepage}
}

% --- Sub-Cover Page (Inner Title Page) ---
\newcommand{\makesubcoverpage}{%
  \begin{titlepage}
    \@drawcoverframe
    \centering
    \vspace*{0.2cm}
    {\fontsize{12}{15}\selectfont\bfseries \@upperuni \par}
    {\fontsize{13}{16}\selectfont\bfseries \@university \par}
    {\fontsize{12}{15}\selectfont\bfseries \@faculty \par}

    \vspace{1.0cm}
    {\fontsize{15}{19}\selectfont\bfseries \@thesistype \par}
    \vspace{0.25cm}
    {\fontsize{12}{15}\selectfont\bfseries \@major \par}

    \vspace{1.2cm}
    \begin{minipage}{0.88\textwidth}
      \centering
      \setstretch{1.35}
      {\fontsize{15}{21}\selectfont\bfseries \@thesistitle \par}
    \end{minipage}

    \vspace{1.4cm}
    \begin{flushleft}
      \hspace{1.4cm}
      \begin{tabular}{@{}l l@{}}
        \textbf{Advisor:}  & \@advisor \\[8pt]
        \textbf{Students:} & \begin{tabular}[t]{@{}l@{}} \@subcoverstudents \end{tabular}
      \end{tabular}
    \end{flushleft}

    \vfill
    {\small\itshape (Sub-cover page -- Add Defense Committee / Reviewer signature blocks per Faculty guidelines if required)\par}
    \vspace{0.8cm}
    {\fontsize{12}{15}\selectfont\bfseries \@place, \@dateyear \par}
    \vspace*{0.2cm}
  \end{titlepage}
}
