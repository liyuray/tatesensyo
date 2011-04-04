#!/usr/bin/perl
use FindBin;
use lib "$FindBin::RealBin/lib";
use Text::sensyo4kindle;
use IPC::Run3;
use File::Temp qw/ tempfile tempdir /;
use strict;
use warnings;
use strict;
use Config;
use CGI qw(:standard);
use Data::Dumper;
use Encode;
use utf8;
use Cwd;
use Sys::Hostname;
use Carp;
$SIG{__DIE__}  = sub { Carp::confess(@_) };
$SIG{__WARN__} = sub { Carp::cluck(@_) };
my $te = 'euc-jp';
my %tc = (
    'sjis' => 'sjis',
    'euc-jp' => 'euc',
    'utf8' => 'utf8',
);
my $root=$FindBin::RealBin;

my $epub_url = param('epub') || "http://wp.1000ebooks.tw/wp-content/plugins/download-monitor/download.php?id=1";
my $devel = param('devel');

#my $tempdir = tempdir( CLEANUP => 1 );
my $tempdir = tempdir( CLEANUP => 0 );
mkdir "$tempdir/log";

$ENV{PATH} = '/usr/local/bin:'.$ENV{PATH} if $^O eq 'darwin';
my @cmd = ("wget", "-O$tempdir/a.epub", $epub_url);
#my @cmd = ("wget", "--trust-server-names", "-P$tempdir", $epub_url);
$ENV{http_proxy} = "http://10.113.2.156:3128" if hostname() =~ /desktop/;
runcmd(\@cmd, 'wget');

@cmd = ("7za", "x", "-o$tempdir/content", "$tempdir/a.epub");
runcmd(\@cmd, '7zax');

my $texfile = "$tempdir/log/a.tex";
my $epubdir = "$tempdir/content";
my ($title, $author) =Text::sensyo4kindle::main($epubdir, $texfile, $te);

$ENV{TEXINPUTS} = "$root:$root/texmf/tex/otf:";
$ENV{TEXFONTS} =  ".:$root/texmf/fonts//:";
@cmd = ("platex", "-kanji=".$tc{$te}, "-output-directory", "$tempdir/log", $texfile);
$ENV{PATH} = "/Applications/pTeX.app/teTeX/bin:".$ENV{PATH} if $^O eq 'darwin';
runcmd(\@cmd, 'platex1');

$ENV{TEXFONTS} =  ".:/usr/share/fonts/truetype//:/usr/share/fonts/opentype//:$root/texmf/fonts//:";
$ENV{CMAPINPUTS} = do {
    if ($^O eq 'darwin') {
        ".:$root/texmf/CMap:/Applications/pTeX.app/teTeX/share/texmf/fonts/cmap/CMap:";
    } else {
        ".:/usr/share/ghostscript/8.71/Resource/CMap:"
    }
};
@cmd = ("dvipdfmx", "-vv", "-f","$root/cid-x.map", "-o", "$tempdir/$title-$author.pdf", "$tempdir/log/a.dvi");
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
