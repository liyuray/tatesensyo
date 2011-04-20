#!/usr/bin/perl
use FindBin;
use lib "$FindBin::RealBin/../lib";
use Text::sensyo4kindle;
use IPC::Run3;
use File::Temp qw/ tempfile tempdir /;
use Encode;
use strict;
use warnings;
use Getopt::Long;
use Carp;
$SIG{__DIE__}  = sub { Carp::confess(@_) };
$SIG{__WARN__} = sub { Carp::cluck(@_) };

die "no epub file specified!" if scalar @ARGV < 1;
#die "no output file!" if scalar @ARGV < 2;

my $verbose;
my $result = GetOptions ( "verbose" => \$verbose );
my $te = 'utf8';
my %tc = (
    'sjis' => 'sjis',
    'euc-jp' => 'euc',
    'utf8' => 'utf8',
);

my $root = $FindBin::RealBin.'/..';

$ENV{PATH} = '/Users/liyuray/texlive/2010/bin/x86_64-darwin:/usr/local/bin:'.$ENV{PATH} if $^O eq 'darwin';
$ENV{PATH} = '/home/yj/e/texlive/bin/x86_64-linux:'.$ENV{PATH} if $^O eq 'linux';

my $tempdir;
for my $epubfile (map { decode 'utf8', $_ } @ARGV) {
    $tempdir = tempdir( CLEANUP => !$verbose );
    mkdir "$tempdir/log";
    my $texfile = "$tempdir/log/a.tex";
    my $epubdir = "$tempdir/content";
    my @cmd = ("7za", "x", "-o$epubdir", $epubfile);
    runcmd(\@cmd, '7zax');

    my ($title, $author) =Text::sensyo4kindle::main($epubdir, $texfile, $te);
    $ENV{TEXINPUTS} = ".:$root:$root/texmf/tex//:";
    $ENV{TEXFONTS} =  ".:$root/texmf/fonts//:";
    @cmd = ("platex",
            "-kanji=".$tc{$te},
            "-shell-escape",
            "-output-directory",
            "$tempdir/log",
            q(\\nonstopmode\\input),
            $texfile,
        );
    runcmd(\@cmd, 'platex1');
    #runcmd(\@cmd, 'platex2');

    $ENV{TEXFONTS} =  "/usr/share/fonts/truetype//:/usr/share/fonts/opentype//:$root/texmf/fonts//:";
    $ENV{CMAPINPUTS} = do {
        if ($^O eq 'darwin') {
#            "$root/texmf/CMap:/Applications/pTeX.app/teTeX/share/texmf/fonts/cmap/CMap:";
#            "$root/texmf/CMap:/Users/liyuray/texlive/2010/texmf/fonts/cmap/dvipdfmx:"
        } else {
            "/usr/share/ghostscript/8.71/Resource/CMap:"
        }
    };
    @cmd = ("dvipdfmx", "-vvvvv", "-f","$root/cid-x.map", "-o", "$title-$author.pdf", "$tempdir/log/a.dvi");
    runcmd(\@cmd, 'dvipdfmx');
}

sub runcmd {
    my $cmdh = shift;
    my $task = shift;
    local $, =' ';
    local $\=$/;

    binmode STDOUT, ':utf8';
    print @$cmdh;
    run3 $cmdh, undef, "$tempdir/log/$task"."out.txt", "$tempdir/log/$task"."err.txt";
#    run3 $cmdh;
}
