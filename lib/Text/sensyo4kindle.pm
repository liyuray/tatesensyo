package Text::sensyo4kindle;
our $VERSION = "0.0001";
BEGIN {
    require 5.006_000;
    use utf8;
    our $matchre = join '', map { "\\$_" } split '',
        '｀…‥’“”〔〕〈〉《》「」『』【】‘’−、。・ー！＃＄％＆（）＋，．：；＝？［］｛｝—～∼─－―⒈⒉⒊⒋⒌⒍⒎⒏⒐⒑⒒⒓⒔⒕⒖⒗⒘⒙⒚⒛　';
    our $matchre1 = qr/([^\x20-\x7e$matchre])/;
#    our $te = "sjis";
}
use strict;
use warnings;
use Encode;
use Data::Dumper;
use File::Basename;
use utf8;

=head1 NAME

Text::sensyo4kindle - vertical TeX for epub

=head1 VERSION

version 0.0001

=cut

use XML::Simple;
use HTML::TreeBuilder;

my $outbuf = "";
sub main {
    my $dir = shift;
    my $texfile = shift;
    my $te = shift;

    my $ref1 = XMLin("$dir/META-INF/container.xml");
    my $opf_file = $ref1->{rootfiles}{rootfile}{'full-path'};
    my $dirname = dirname("$dir/$opf_file");
    my $ref = XMLin("$dir/$opf_file");
    my $title = ref($ref->{metadata}{'dc:title'}) eq 'HASH'
        ? $ref->{metadata}{'dc:title'}{content}
            : $ref->{metadata}{'dc:title'};
    my $author = ref($ref->{metadata}{'dc:creator'}) eq 'HASH'
        ? $ref->{metadata}{'dc:creator'}{content}
            : $ref->{metadata}{'dc:creator'};
    my $cover = $ref->{metadata}{meta}{cover}{content} if exists $ref->{metadata}{meta}{cover};
    my @content_files = map { "$dirname/".$ref->{manifest}{item}{$_->{idref}}{href} } @{$ref->{spine}{itemref}};

    binmode STDOUT, ':utf8';
    binmode STDERR, ':utf8';
    for my $file (@content_files) {
#        print $file,$/;
        my $tree = HTML::TreeBuilder->new; # empty tree
        open my $fh, "<:utf8", $file or die $!;
        $tree->parse_file($fh);
#        $tree->dump;
#        exit 1;
        my ($head, $body) = map {
            $tree->look_down( '_tag' , $_ )
        } qw(head body);

        my $title = $head->look_down( '_tag', 'title' );
        if ($title) {
            my $titlestring = $title->as_text;
            if ($titlestring and $file =~/Section\d+/) {
                $outbuf .= "\\subtitle{".encode_chinese( $titlestring )."}".$/;
            }
        }
        process_body($body);
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

sub process_node {
    my $x = $_[0];
    my $l = $_[1];
    
#    print ' 'x$l,$x->tag,$/;
    if ($x->tag eq 'h1') {
        $outbuf .= q(\begin{jisage}{0}).$/;
        $outbuf .= "{\\Large ".encode_chinese( $x->as_text )."}$/";
        $outbuf .= q(\end{jisage}).$/;
        $outbuf .= q(\par\vspace{1\baselineskip}).$/; # one line space
    } elsif ($x->tag eq 'h2') {
        $outbuf .= q(\newpage).$/;
        $outbuf .= q(\begin{jisage}{0}).$/;
        $outbuf .= "{\\large ".encode_chinese( $x->as_text )."}$/";
        $outbuf .= q(\end{jisage}).$/;
        $outbuf .= q(\par\vspace{1\baselineskip}).$/; # one line space
    } elsif ($x->tag eq 'p') {
        foreach my $c ($x->content_list) {
            print(' ' x $l, $x->tag,"+-", substr($c,0,20), $/) if not ref $c;;
            $outbuf .= output( $c ).$/.$/ if not ref $c;
            process_node($c, $l+1) if ref $c; #ignore text notes
        }
    } else {
        foreach my $c ($x->content_list) {
            print(' ' x $l, $x->tag,"--", substr($c,0,20), $/) if not ref $c;;
#            $outbuf .= output( $c ).$/.$/ if not ref $c;
            process_node($c, $l+1) if ref $c; #ignore text notes
        }            
    }
}

sub process_body {
    my $body = shift;

    process_node($body, 0);
}

sub encode_chinese {
    my $s = shift;
    (my $ret = $s) =~ s/$Text::sensyo4kindle::matchre1/sprintf("\\UTFT{%X}",ord $1)/ge;
    return $ret;
}

sub output {
    my $plain_text = shift;

    my $ret1 = encode_chinese($plain_text);
    $ret1 =~ s/(?:——|――|－－|──|──)/\\――{}/g;      # tricky: use 0x2015 for euc-jp conversion
    $ret1 =~ s/～/〜/g;          # tricky: use WAVE DASH
    $ret1 =~ s/！！！/\\rensuji{!!!}/g;
    $ret1 =~ s/！！/\\rensuji{!!}/g;
    $ret1 =~ s/？！/\\rensuji{?!}/g;
    $ret1 =~ s/！？/\\rensuji{!?}/g;
    $ret1 =~ s/？？/\\rensuji{??}/g;
    $ret1 =~ s/([？！])/$1\\</g; # prevent redundant space after !?
    $ret1 =~ s/\&hellip\;/……/g;
    $ret1 =~ s/\&/\\\&/g;
    $ret1 =~ s/\［/\〔/g;
    $ret1 =~ s/\］/\〕/g;
    $ret1 =~ s/　{2,}/ /g;    # dirty
#    $ret1 =~ s/\b(\d)\.([^\d])/sprintf("\\UTF{%X}", $1 - 1 + ord('⒈')).$2/ge; #between 1 and 20 ⒈=0x2488, １=0xff11
#    $ret1 =~ s/\b(\d\d)\.([^\d])/sprintf("\\UTF{%X}", $1 - 1 + ord('⒈')).$2/ge; #between 1 and 20 ⒈=0x2488, １=0xff11
    $ret1 =~ s/\b(\d)\.([^\d])/sprintf("\\rensuji{\\UTF{%X}\\kern-.3zw .}", $1 - 1 + ord('１')).$2/ge; #between 1 and 20 ⒈=0x2488, １=0xff11
#    $ret1 =~ s/\b(\d)\.([^\d])/\\ajPeriod{$1}$2/g; #between 1 and 20 ⒈=0x2488, １=0xff11
    $ret1 =~ s/\b(\d\d)\.([^\d])/\\rensuji{$1\\kern-.1zw \.}$2/g;
    return $ret1;
}

sub gen_tex {
    my $title = shift;
    my $author = shift;
    my $te = shift;

    my $t1 = encode_chinese($title);
    my $a1 = encode_chinese($author);
    my $tex = << 'TEX';
\documentclass[a5paper]{tbook}
\usepackage[noreplace, multi]{otf}
\usepackage[device=kindle2,size=large]{sensyo}
\usepackage{times}
\usepackage{atbegshi}
%% Bookmarkの文字化け対策（日本語向け）
\ifnum 46273=\euc"B4C1 % 46273 == 0xB4C1 == 漢(EUC-JP)
  \AtBeginShipoutFirst{\special{pdf:tounicode EUC-UCS2}}%
\else
  \AtBeginShipoutFirst{\special{pdf:tounicode 90ms-RKSJ-UCS2}}%
\fi
\usepackage[dvipdfm,bookmarks=false,bookmarksnumbered=false,hyperfootnotes=false,%
TEX
    my $tex1 = << "TEX1";
pdftitle={$title},%
pdfauthor={$author},%
pdfcreator={縱覽千書 v$VERSION},%
pdfproducer={縱覽千書 v$VERSION},%
pdfkeywords={}]{hyperref}

\\title{$t1}
\\author{$a1}
TEX1
    my $tex2 = << 'TEX2';
\date{}
\begin{document}
%\DeclareGraphicsRule{JPG}{jpg}{*}{}
\maketitle
\setlength{\parindent}{2zw}
TEX2
    return encode($te,$tex.$tex1.$tex2);
}

=head1 SYNOPSIS

Quick summary of what the module does.

Perhaps a little code snippet.

    use Text::sensyo4kindle;

    my $foo = Text::sensyo4kindle->new();
    ...

=head1 EXPORT

A list of functions that can be exported.  You can delete this section
if you don't export anything, such as for a purely object-oriented module.

=head1 SUBROUTINES/METHODS

=head2 function1

=cut

sub function1 {
}

=head2 function2

=cut

sub function2 {
}

=head1 AUTHOR

Liyuray Li, C<< <liyuray at gmail.com> >>

=head1 BUGS

Please report any bugs or feature requests to C<bug-text-sensyo4kindle at rt.cpan.org>, or through
the web interface at L<http://rt.cpan.org/NoAuth/ReportBug.html?Queue=Text-sensyo4kindle>.  I will be notified, and then you'll
automatically be notified of progress on your bug as I make changes.




=head1 SUPPORT

You can find documentation for this module with the perldoc command.

    perldoc Text::sensyo4kindle


You can also look for information at:

=over 4

=item * RT: CPAN's request tracker (report bugs here)

L<http://rt.cpan.org/NoAuth/Bugs.html?Dist=Text-sensyo4kindle>

=item * AnnoCPAN: Annotated CPAN documentation

L<http://annocpan.org/dist/Text-sensyo4kindle>

=item * CPAN Ratings

L<http://cpanratings.perl.org/d/Text-sensyo4kindle>

=item * Search CPAN

L<http://search.cpan.org/dist/Text-sensyo4kindle/>

=back


=head1 ACKNOWLEDGEMENTS


=head1 LICENSE AND COPYRIGHT

Copyright 2011 Liyuray Li.

This program is free software; you can redistribute it and/or modify it
under the terms of either: the GNU General Public License as published
by the Free Software Foundation; or the Artistic License.

See http://dev.perl.org/licenses/ for more information.


=cut

1;

__END__
