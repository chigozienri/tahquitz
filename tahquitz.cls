\pdfminorversion=4 % force pdf 1.4 output; http://tex.stackexchange.com/questions/95973/is-pdftex-1-40-13-outputting-malformed-pdfs

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{tahquitz}

\LoadClass[11pt]{book}
% Note that 11 pt does work with pdflatex, even though 11 pt is not one of the sizes
% of CM. I don't know whether it scales up 10 pt or scales down 12 pt, but anyway, it
% works.

%===============================================
\usepackage{graphicx,url,ifthen,wrapfig}
%-----------------------------------
\usepackage{geometry} % https://www.sharelatex.com/learn/Page_size_and_margins
\geometry{margin=0.75in}
%-----------------------------------
\usepackage{tocloft}
\renewcommand\numberline[1]{} % https://tex.stackexchange.com/questions/218663/remove-section-number-from-table-of-contents
%===============================================
\newcommand{\normalparindent}{\setlength{\parindent}{0pt}\parskip 0pt}
\newcommand{\discussionparindent}{\setlength{\parindent}{0pt}\parskip 4pt}
\normalparindent
\pagestyle{plain} % https://tex.stackexchange.com/questions/120746/removing-headers-keeping-page-numbers-in-the-same-time
%-----------------------------------
% https://stackoverflow.com/questions/38292590/remove-section-numbers-latex
\makeatletter
\renewcommand{\@seccntformat}[1]{}
\makeatother
%-----------------------------------
\newcommand{\pitch}[1]{\textbf{P#1}.}
\newcommand{\variation}[1]{\textit{Var #1\/}:}
\newcommand{\warn}[1]{\textbf{Warning: #1}}
%===============================================
\newcommand{\myfooter}{\hfill\footnotesize{Ben Crowell, github.com/bcrowell/tahquitz}}
\newcommand{\climb}[3][0]{\ifthenelse{\equal{#1}{1}}{}{\myfooter\vfill}\clearpage\section{#2 (#3)}}
\newcommand{\topo}[2]{% #1=width as a fraction of textwidth, typically about 0.4
  \begin{wrapfigure}{l}{#1\textwidth}
    \includegraphics[width=\linewidth]{figs/#2}
  \end{wrapfigure}
}
\newenvironment{mytable}[1]{\vspace{3mm}\emph{#1}\\}{\vspace{3mm}}
