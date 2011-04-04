#!/usr/bin/perl
use Text::sensyo4kindle;
use IPC::Run3;
use File::Temp qw/ tempfile tempdir /;

die "no epub file specified!" if scalar @ARGV < 1;
die "no output file!" if scalar @ARGV < 2;
my $epubfile = $ARGV[0];
my $texfile = $ARGV[1];

my $tempdir = tempdir( CLEANUP => 1 );
mkdir "$tempdir/log";
my $epubdir = "$tempdir/content";
my @cmd = ("7za", "x", "-o$epubdir", $epubfile);
runcmd(\@cmd, '7zax');

Text::sensyo4kindle::main($epubdir, $texfile);

sub runcmd {
    my $cmdh = shift;
    my $task = shift;
#    run3 $cmdh, undef, "$tempdir/log/$task"."out.txt", "$tempdir/log/$task"."err.txt";
    run3 $cmdh;
}
