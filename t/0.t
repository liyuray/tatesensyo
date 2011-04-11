use Test::More tests => 4;
use utf8;

BEGIN {
    use_ok( 'Text::sensyo4kindle' );
}

ok (q(\UTFT{6211}) eq Text::sensyo4kindle::encode_chinese('我'));
ok (q(\――{}) eq Text::sensyo4kindle::output('——') );
ok (q(\――{}) eq Text::sensyo4kindle::output('──') );
