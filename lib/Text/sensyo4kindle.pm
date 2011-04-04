package Text::sensyo4kindle;
BEGIN {
    require 5.006_000;
    use utf8;
    our $matchre = join '', map { "\\$_" } split '',
        '｀…‥’“”〔〕〈〉《》「」『』【】‘’−、。・ー！＃＄％＆（）＋，．：；＝？［］｛｝—～∼';
    our $puncts = '｀…‥’“”〔〕〈〉《》「」『』【】‘’−、。・ー！＃＄％＆（）＋，．：；＝？［］｛｝—～∼';
    our $matchre1 = qr/([^\x20-\x7e$matchre])/;
#    our $te = "sjis";
} # i.e. 5.6.0
use strict;
use warnings;
use Encode;
use utf8;

=head1 NAME

Text::sensyo4kindle - vertical TeX for epub

=head1 VERSION

version 0.001

=cut

our $VERSION = '0.001';

use XML::Simple;
use HTML::TreeBuilder;

sub main {
    my $dir = shift;
    my $texfile = shift;
    my $te = shift;

    my $ref = XMLin("$dir/OEBPS/content.opf");

    my $title = $ref->{metadata}{'dc:title'};
    my $author = ref($ref->{metadata}{'dc:creator'}) eq 'HASH'
        ? $ref->{metadata}{'dc:creator'}{content}
            : $ref->{metadata}{'dc:creator'};
    my @content_files = map { "$dir/OEBPS/".$ref->{manifest}{item}{$_->{idref}}{href} } @{$ref->{spine}{itemref}};

#    print @content_files;
#    exit 1;
    my $outbuf = "";
    for my $file (@content_files) {
        print $file,$/;
        my $tree = HTML::TreeBuilder->new; # empty tree
        $tree->parse_file($file);
#        $tree->dump;
#        exit 1;
        my %content = map {
            $_ => [$tree->look_down( '_tag' , $_ )];
        } qw(title h1 h2 p);
        if ($content{title}[0]->as_text and $file =~/Section\d+/) {
            $outbuf .= "\\subtitle{".encode_chinese(decode('utf8',$content{title}[0]->as_text))."}".$/;
        }
#        $outbuf .= output( $te, decode( 'utf8', $content{title}[0]->as_text ) )."$/$/";
        if (defined $content{h1}[0] and $content{h1}[0]->as_text) {
            $outbuf .= q(\begin{jisage}{0}).$/;
            $outbuf .= "{\\Large ".encode_chinese(decode('utf8',$content{h1}[0]->as_text))."}$/";
            $outbuf .= q(\end{jisage}).$/.$/;
            $outbuf .= q(\par\vspace{8mm}).$/;
        }
        for my $item (@{$content{p}}) {
            $outbuf .= output( $te, decode('utf8', $item->as_text) );
            #            print $item->as_text;
            $outbuf .= "$/$/";
        }
        #        print $tag, ":", map { defined $_ && ref $_ eq 'HASH' && $_->as_text } @{$content{$tag}}, $/;
        $outbuf .= '\clearpage'.$/.$/;
        $tree = $tree->delete;
    }

    my $fho;
    open $fho, ">:raw", $texfile or die "$!";
    print $fho gen_tex(
        $title,
        $author,
        $te,
    );
    print $fho encode($te,$outbuf);
    print $fho '\end{document}',$/;
    close $fho;
    return $title, $author;
}

sub encode_chinese {
    my $s = shift;
    (my $ret = $s) =~ s/$Text::sensyo4kindle::matchre1/sprintf("\\UTFT{%X}",ord $1)/ge;
    return $ret;
}

sub gen_tex {
    my $title = shift;
    my $author = shift;
    my $te = shift;

    my $t1 = encode('ascii', $title,  sub { sprintf "\\UTFT{%X}", $_[0] });
    my $a1 = encode('ascii', $author, sub { sprintf "\\UTFT{%X}", $_[0] });
    my $tex = << 'TEX';
\documentclass[a5paper]{tbook}
\usepackage[noreplace, multi]{otf}
\usepackage[device=kindle2,size=large]{sensyo}
%\usepackage{atbegshi}
%\AtBeginShipoutFirst{\special{pdf:tounicode EUC-UCS2}}
%\usepackage[dvipdfm,%
\usepackage[dvipdfm,bookmarks=false,bookmarksnumbered=false,hyperfootnotes=false,%
TEX
    my $tex1 = << "TEX1";
pdftitle={$title},%
pdfauthor={$author},%
pdfkeywords={}]{hyperref}
%% Bookmarkの文字化け対策（日本語向け）
\\ifnum 46273=\\euc"B4C1 % 46273 == 0xB4C1 == 漢(EUC-JP)
  \\AtBeginDvi{\\special{pdf:tounicode EUC-UCS2}}%
\\else
  \\AtBeginDvi{\\special{pdf:tounicode 90ms-RKSJ-UCS2}}%
\\fi

\\title{$t1}
\\author{$a1}
TEX1
    my $tex2 = << 'TEX2';
\date{}
\begin{document}
\maketitle
\setlength{\parindent}{2em}
TEX2
    return encode($te,$tex.$tex1.$tex2);
}

sub output {
    my $te = shift;
    my $plain_text = shift;

    my $ret1 = encode_chinese($plain_text);
#    binmode STDOUT, ":utf8";
#    print($ret1, $/);
#    exit 1;
#    $ret =~ s/$matchre/chr(hex($1))/ge;
#    print($ret, $/) if $ret =~ /—/;
    $ret1 =~ s/——/\\――{}/g;      # tricky: use 0x2015 for euc-jp conversion
    $ret1 =~ s/～/〜/g;          # tricky: use WAVE DASH
    $ret1 =~ s/！！！/\\rensuji{!!!}/g;
#    binmode STDOUT, ":raw";
#    print(encode($te, $ret), $/), exit 1 if $ret =~ /—/;
#    $ret =~ s/([\？\！])　/$1{}/g;
#    $ret =~ s/？　/？{}/g;
#    $ret =~ s/！　/！{}/g;
#    print $ret;
#    exit 1;
#    $ret1 = encode( $te, $ret1);
    return $ret1;
}

1;

__END__
