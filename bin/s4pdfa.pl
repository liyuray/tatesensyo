#!/usr/bin/perl
use Text::sensyo4kindle;
use IPC::Run3;
use File::Temp qw/ tempfile tempdir /;
use strict;
use warnings;

die "no epub file specified!" if scalar @ARGV < 1;
#die "no output file!" if scalar @ARGV < 2;

my $te = 'euc-jp';
my %tc = (
    'sjis' => 'sjis',
    'euc-jp' => 'euc',
    'utf8' => 'utf8',
);
my $tempdir;
for my $epubfile (@ARGV) {
    $tempdir = tempdir( CLEANUP => 1 );
    mkdir "$tempdir/log";
    my $texfile = "$tempdir/log/a.tex";
    my $epubdir = "$tempdir/content";
    my @cmd = ("7za", "x", "-o$epubdir", $epubfile);
    runcmd(\@cmd, '7zax');

    my ($title, $author) =Text::sensyo4kindle::main($epubdir, $texfile, $te);
    $ENV{TEXINPUTS} = ".:./tatesensyo:./tatesensyo/texmf/tex//:";
    $ENV{TEXFONTS} =  ".:./tatesensyo/texmf/fonts//:";
    @cmd = ("platex", "-kanji=".$tc{$te}, "-output-directory", "$tempdir/log", $texfile);
    runcmd(\@cmd, 'platex1');
    #runcmd(\@cmd, 'platex2');

    $ENV{TEXFONTS} =  ".:/usr/share/fonts/truetype//:/usr/share/fonts/opentype//:./tatesensyo/texmf/fonts//:";
    #$ENV{CMAPINPUTS} = ".:/usr/share/ghostscript/8.71/Resource/CMap:";
    $ENV{CMAPINPUTS} = ".:./tatesensyo/texmf/CMap:/Applications/pTeX.app/teTeX/share/texmf/fonts/cmap/CMap:";
    @cmd = ("dvipdfmx", "-vvvvv", "-f","./tatesensyo/cid-x.map", "-o", "$title-$author.pdf", "$tempdir/log/a.dvi");
    runcmd(\@cmd, 'dvipdfmx');
}

sub runcmd {
    my $cmdh = shift;
    my $task = shift;
    local ($, =' ', $\=$/);
    print @$cmdh;
    run3 $cmdh, undef, "$tempdir/log/$task"."out.txt", "$tempdir/log/$task"."err.txt";
#    run3 $cmdh;
}
