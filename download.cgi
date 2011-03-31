#!/usr/bin/perl
use strict;
use warnings;
use Config;
use IPC::Run3;
use CGI qw(:standard);
use File::Temp qw/ tempfile tempdir /;
use XML::Simple;
use Data::Dumper;
use Encode;
use utf8;
use HTML::TreeBuilder;
use Cwd;
use Carp;
$SIG{__DIE__}  = sub { Carp::confess(@_) };
$SIG{__WARN__} = sub { Carp::cluck(@_) };

#my $dir = getcwd;

#print "Content-type: text/html\n\n";
#print $dir;

my $tex = << 'TEX';
\documentclass[a5paper]{tbook}
%\\documentclass[a5paper, twocolumn]{tbook}
\usepackage[deluxe,multi]{otf}
%\\usepackage[expert, deluxe]{otf}
%##MyAUTHOR##
%\\usepackage{utf}
%\\usepackage{furikana}
%\\usepackage{type1cm}
%\\def\\rubykatuji{\\rubyfamily\\tiny}
%\\def\\rubykatuji{\\tiny}%for UTF package
%\\renewenvironment{teihon}{\\comment}{\\endcomment}

\usepackage[device=kindle2,size=large]{sensyo}
\title{hlhz}
\author{xh}
\date{}
\begin{document}
\setlength{\parindent}{2em}
%\includegraphics[angle=90, width=10cm, height=10cm]{hlhz/OEBPS/Images/Cover.png}
%\maketitle
%\tableofcontents
%\pagestyle{empty}
%\pagenumbering{gobble}
%\tchrm
%\large
%\bf
\input{a.txt}
\end{document}

TEX

my $text_encoding = "euc-jp";
my $plain_encoding = "ascii";
#umask 0666;
#umask 0750;

my $epub_url = param('epub') || "http://wp.1000ebooks.tw/wp-content/plugins/download-monitor/download.php?id=4";
my $devel = param('devel');

my $tempdir = tempdir( CLEANUP => 1 );
#my $tempdir = tempdir( CLEANUP => 0 );
mkdir "$tempdir/log";

my @cmd = ("wget", "-O$tempdir/a.epub", $epub_url);
#my @cmd = ("wget", "--trust-server-names", "-P$tempdir", $epub_url);
my ($in,$out,$err);
#$ENV{http_proxy} = "http://10.113.2.156:3128";
runcmd(\@cmd, 'wget');

@cmd = ("7za", "x", "-o$tempdir/content", "$tempdir/a.epub");
runcmd(\@cmd, '7zax');

my $ref = XMLin("$tempdir/content/OEBPS/toc.ncx");
my $navpoint = $ref->{navMap}{navPoint};
my @order = sort {$navpoint->{$a}{playOrder} <=> $navpoint->{$b}{playOrder}} (keys %{$navpoint});
my @content_files = map { "$tempdir/content/OEBPS/".$navpoint->{$_}{content}{src} } @order;
my $outbuf = "";
for my $file (@content_files) {
#    print $file,$/;
    my $tree = HTML::TreeBuilder->new; # empty tree
    $tree->parse_file($file);
#    $tree->dump;
    my %content = map {
        $_ => [$tree->look_down( '_tag' , $_ )];
    } qw(title h1 h2 p);
    #    print Dumper(\%content);
    #    for my $tag qw(title h1 h2 h3) {
    $outbuf .= output("\\chapter{".
                     decode('utf8',$content{title}[0]->as_text)
                         ."}").$/;
    for my $item (@{$content{p}}) {
        $outbuf .= output(decode('utf8', $item->as_text));
        #            print $item->as_text;
        $outbuf .= "$/$/";
    }
#        print $tag, ":", map { defined $_ && ref $_ eq 'HASH' && $_->as_text } @{$content{$tag}}, $/;
    $tree = $tree->delete;
}

my $fho;
open $fho, ">:raw", "$tempdir/a.txt" or die "$!";
print $fho $outbuf;
close $fho;

open $fho, ">:utf8", "$tempdir/a.tex" or die "$!";
print $fho $tex;
close $fho;

#chdir $tempdir;
@cmd = ("cp", "./tatesensyo/sensyo.sty", $tempdir);
runcmd(\@cmd, 'cp');

$ENV{TEXINPUTS} = ".:/home/ubuntu/.texmf-var/tex/otf:";
$ENV{TEXFONTS} =  ".:/home/ubuntu/.texmf-var/fonts//:";
@cmd = ("platex", "-output-directory", $tempdir, "$tempdir/a.tex");
runcmd(\@cmd, 'platex');

$ENV{TEXFONTS} =  ".:/usr/share/fonts/truetype//:/usr/share/fonts/opentype//:/home/ubuntu/.texmf-var/fonts//:";
$ENV{CMAPINPUTS} = ".:/usr/share/ghostscript/8.71/Resource/CMap:";
@cmd = ("dvipdfmx", "-vv", "-z", "9", "-f","./tatesensyo/cid-x.map", "-o", "$tempdir/a.pdf", "$tempdir/a.dvi");
runcmd(\@cmd, 'dvipdfmx');

my $outfile;
if (-r "$tempdir/a.pdf" and !$devel) {
    $outfile = "$tempdir/a.pdf";
} else {
    @cmd = ("7za", "a", "$tempdir/log.7z", "$tempdir/log");
    run3 \@cmd, undef, "/dev/null", "/dev/null";
    $outfile = "$tempdir/log.7z";
}

die "no $outfile!$/" unless -r $outfile;

my $fh;
open $fh, "<:raw", $outfile or die $!;
my $file_content = do { local $/; <$fh> };
print "Content-Type:application/x-download\n";   
print "Content-Disposition:attachment;filename=$outfile\n\n";  
binmode STDOUT, ':raw';
print $file_content;

sub runcmd {
    my $cmdh = shift;
    my $task = shift;
    run3 $cmdh, undef, "$tempdir/log/$task"."out.txt", "$tempdir/log/$task"."err.txt";
}

sub output {
    my $plain_text = shift;
    return
        encode($text_encoding, decode($plain_encoding,
                                      encode(
                                          $plain_encoding,
                                          $plain_text,
                                          #			Encode::FB_PERLQQ
                                          sub { sprintf "\\UTFT{%X}",$_[0]	}
                                      )
                                  ));
}



__END__


__END__

foreach my $key (sort keys(%ENV)) {
#  print "$key = $ENV{$key}<p>";
}
foreach my $key (sort keys(%Config)) {
  print "$key = $Config{$key}<p>" if defined $Config{$key};
}

