export declare function cleanObject(obj: any): void;
export declare function diagnoseJsonPath(data: any, path: string[]): string;
export declare function pickBySchema(obj: any, schema: any): any;
export declare function flattenArraysInObject(input: any, inArray?: boolean): any;
/**
 * Airbnb moved several PDP sections to client-side rendering. Their entries under
 * `presentation.stayProductDetailPage.sections.sections` still exist, still report
 * sectionContentStatus COMPLETE, but carry a `section` object containing nothing but
 * `__typename`. AMENITIES_DEFAULT and HIGHLIGHTS_DEFAULT are both in that state, so
 * the schema-driven extraction returns an empty shell rather than failing loudly.
 *
 * The content now lives on a sibling branch of the same payload:
 *   niobeClientData[i][1].data.node.pdpPresentation
 *
 * Returns null when the branch is absent, so callers fall back to whatever the
 * section tree gave them rather than losing data if Airbnb moves it again.
 */
export declare function findPdpPresentation(clientData: any): any | null;
/**
 * Amenity groups, preserving each item's `available` flag.
 *
 * The flag is the whole point: Airbnb renders unavailable amenities struck through,
 * and a listing that advertises air conditioning in its description while carrying
 * `available: false` on the amenity is the exact case a reader needs to catch.
 * Grouping by availability makes that impossible to skim past, where a flat list of
 * titles would quietly assert the opposite of the truth.
 */
export declare function extractAmenities(pdp: any): any | null;
/**
 * Turn `[{ title: "Bathroom", amenities: [...] }, ...]` into `{ Bathroom: [...], ... }`.
 *
 * The category is the useful part of an amenity list, and as an array element its title
 * survives only as a prefix inside one long joined string — a consumer that wants the
 * bathroom amenities has to parse them back out, and cannot tell a category boundary
 * from a comma inside a category. As an object key it is addressable directly, and
 * flattenArraysInObject leaves top-level keys alone, so each category flattens to its
 * own string. Airbnb's own "Not included" group lands here like any other category.
 *
 * Applied to both the section tree and the recovered pdpPresentation content so the two
 * paths cannot disagree about the shape. Untitled groups fall back to "Other" rather
 * than being dropped, and duplicate titles merge instead of overwriting.
 */
export declare function keyAmenityGroups(section: any): any;
export declare function extractHighlights(pdp: any): any | null;
