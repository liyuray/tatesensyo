#!perl -T

use Test::More tests => 1;

BEGIN {
    use_ok( 'Text::sensyo4kindle' ) || print "Bail out!\n";
}

diag( "Testing Text::sensyo4kindle $Text::sensyo4kindle::VERSION, Perl $], $^X" );
