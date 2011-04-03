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
use Sys::Hostname;
use Carp;
$SIG{__DIE__}  = sub { Carp::confess(@_) };
$SIG{__WARN__} = sub { Carp::cluck(@_) };

#my $dir = getcwd;

#print "Content-type: text/html\n\n";
#print $dir;
my $puncts = '｀…‥‘’“”〔〕〈〉《》「」『』【】‘’−、。・ー！＃＄％＆（）＋，．：；＝？［］｛｝—';
my $matchre = join "|", map { sprintf("%X", ord) } split '', $puncts;
$matchre = qr/\\UTFT\{($matchre)\}/;
#print $matchre;
#exit 1;

my $text_encoding = "euc-jp";
my $plain_encoding = "ascii";
#umask 0666;
#umask 0750;

my $epub_url = param('epub') || "http://wp.1000ebooks.tw/wp-content/plugins/download-monitor/download.php?id=1";
my $devel = param('devel');

my $tempdir = tempdir( CLEANUP => 1 );
#my $tempdir = tempdir( CLEANUP => 0 );
mkdir "$tempdir/log";

my @cmd = ("wget", "-O$tempdir/a.epub", $epub_url);
#my @cmd = ("wget", "--trust-server-names", "-P$tempdir", $epub_url);
my ($in,$out,$err);
$ENV{http_proxy} = "http://10.113.2.156:3128" if hostname() =~ /desktop/;
runcmd(\@cmd, 'wget');

@cmd = ("7za", "x", "-o$tempdir/content", "$tempdir/a.epub");
runcmd(\@cmd, '7zax');

my $ref = XMLin("$tempdir/content/OEBPS/content.opf");

my $title = $ref->{metadata}{'dc:title'};
my $author = $ref->{metadata}{'dc:creator'}{content};
my @content_files = map { "$tempdir/content/OEBPS/".$ref->{manifest}{item}{$_->{idref}}{href} } @{$ref->{spine}{itemref}};

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
                          decode('utf8', $content{title}[0]->as_text)
                              ."}").$/;
    for my $item (@{$content{p}}) {
        $outbuf .= output( decode('utf8', $item->as_text) );
        #            print $item->as_text;
        $outbuf .= "$/$/";
    }
#        print $tag, ":", map { defined $_ && ref $_ eq 'HASH' && $_->as_text } @{$content{$tag}}, $/;
    $tree = $tree->delete;
}

my $fho;
open $fho, ">:raw", "$tempdir/log/a.txt" or die "$!";
print $fho $outbuf;
close $fho;

gen_tex(
    encode('ascii', $title,  sub { sprintf "\\UTFT{%X}", $_[0] }),
    encode('ascii', $author, sub { sprintf "\\UTFT(%X)", $_[0] }),
    encode('euc-jp', $title),
    encode('euc-jp', $author),
);

$ENV{TEXINPUTS} = ".:./tatesensyo:./tatesensyo/texmf/tex/otf:";
$ENV{TEXFONTS} =  ".:./tatesensyo/texmf/fonts//:";
@cmd = ("platex", "-output-directory", $tempdir, "$tempdir/log/a.tex");
runcmd(\@cmd, 'platex1');
#runcmd(\@cmd, 'platex2');

$ENV{TEXFONTS} =  ".:/usr/share/fonts/truetype//:/usr/share/fonts/opentype//:./tatesensyo/texmf/fonts//:";
$ENV{CMAPINPUTS} = ".:/usr/share/ghostscript/8.71/Resource/CMap:";
@cmd = ("dvipdfmx", "-vv", "-z", "9", "-f","./tatesensyo/cid-x.map", "-o", "$tempdir/$title-$author.pdf", "$tempdir/a.dvi");
runcmd(\@cmd, 'dvipdfmx');

my $outfile;
if (-r "$tempdir/$title-$author.pdf" and !$devel) {
    $outfile = "$tempdir/$title-$author.pdf";
} else {
    @cmd = ("7za", "a", "-tzip", "$tempdir/log.zip", "$tempdir/log");
    run3 \@cmd, undef, "/dev/null", "/dev/null";
    $outfile = "$tempdir/log.zip";
}

die "no $outfile!$/" unless -r $outfile;

my $fh;
open $fh, "<:raw", $outfile or die $!;
my $file_content = do { local $/; <$fh> };
binmode STDOUT, ":utf8";
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
    my $ret =
        decode( 'utf8',
                encode(
                    $plain_encoding,
                    $plain_text,
                    #			Encode::FB_PERLQQ
                    sub { sprintf "\\UTFT{%X}",$_[0]	}
                )
            );
#    binmode STDOUT, ":utf8";
#    print($ret, $/) if $ret =~ /\{2014\}/;
    $ret =~ s/$matchre/chr(hex($1))/ge;
#    print($ret, $/) if $ret =~ /—/;
    $ret =~ s/——/\\――{}/g;      # tricky: use 0x2015 for euc-jp conversion
#    binmode STDOUT, ":raw";
#    print(encode('euc-jp', $ret), $/), exit 1 if $ret =~ /—/;
#    $ret =~ s/([\？\！])　/$1{}/g;
    $ret =~ s/？　/？{}/g;
    $ret =~ s/！　/！{}/g;
    
#    print $ret;
#    exit 1;
    $ret = encode( $text_encoding, $ret);
    return $ret;
}

sub gen_tex {
    my $title = shift;
    my $author = shift;
    my $tj = shift;
    my $aj = shift;
    my $tex = << 'TEX';
\documentclass[a5paper]{tbook}
\usepackage[noreplace, multi]{otf}
\usepackage[device=kindle2,size=large]{sensyo}
\usepackage{atbegshi}
\AtBeginShipoutFirst{\special{pdf:tounicode EUC-UCS2}}
\usepackage[dvipdfm,%
TEX
    my $tex1 = << "TEX1";
pdftitle={$tj},%
pdfsubject={},%
pdfauthor={$aj},%
pdfkeywords={}]{hyperref}

\\title{$title}
\\author{$author}
TEX1
    my $tex2 = << 'TEX2';
\date{}
\begin{document}
\setlength{\parindent}{2em}
\input{log/a.txt}
\end{document}
TEX2
    open $fho, ">:raw", "$tempdir/log/a.tex" or die "$!";
    print $fho $tex,$tex1,$tex2;
    close $fho;
}

__END__


__END__

foreach my $key (sort keys(%ENV)) {
#  print "$key = $ENV{$key}<p>";
}
foreach my $key (sort keys(%Config)) {
  print "$key = $Config{$key}<p>" if defined $Config{$key};
}

